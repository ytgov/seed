# -*- coding: utf-8 -*-
"""
:copyright (c) 2014 - 2018, The Regents of the University of California, through Lawrence Berkeley National Laboratory (subject to receipt of any required approvals from the U.S. Department of Energy) and contributors. All rights reserved.  # NOQA
:author
"""

from collections import defaultdict

from django.core.management.base import BaseCommand

from seed.data_importer.equivalence_partitioner import EquivalencePartitioner
from seed.lib.superperms.orgs.models import (
    Organization
)
from seed.models import (
    Property,
    PropertyState,
    PropertyView,
    TaxLot,
    TaxLotState,
    TaxLotView,
)


class Command(BaseCommand):
    help = 'Associates -States across Cycles using Property/TaxLot models and -Views. Labels for associated -States become aligned across Cycles.'

    def add_arguments(self, parser):
        parser.add_argument('--organization',
                            help='Organization Name - If none is provided, this script is executed on all organizations.',
                            action='store')

        parser.add_argument('--yes',
                            help='respond "y" (yes) to all confirmation prompts',
                            action='store_true')

    def handle(self, *args, **options):
        organization_name = options.get('organization', None)
        yes_flag = options.get('yes', False)

        if organization_name is None:
            self._no_org_provided(yes_flag)
        elif Organization.objects.filter(name=organization_name).exists():
            org = Organization.objects.get(name=organization_name)
            self._associate_states(org)
        else:
            self.stdout.write(
                '%s is not an existing Organization.' % organization_name,
                ending='\n'
            )

    def _no_org_provided(self, yes_flag):
        def execute_for_all_orgs():
            for org in Organization.objects.all():
                self._associate_states(org)

        self.stdout.write(
            'This will execute the script for all organizations.',
            ending='\n'
        )

        if yes_flag:
            execute_for_all_orgs()
        else:
            if input('Are you sure?(y/n): ') == 'y':
                execute_for_all_orgs()
            else:
                return


    def _associate_states(self, org):
        """
        Starting with org
            - grab all Properties and their PropertyViews
                - Group IDs by matching criteria
                    - for each View, get State comparison keys
                    - add to defaultdict where key = comparison-key and value = list of view objects
                - For each list,
                    - Take the "first Property" and associate that to the rest of the PropertyViews in this Group
                    - grab all Labels associated to any Properties within this PropertyViews and apply those to that "first Property"
            - repeat for TaxLotViews
        """
        self.stdout.write(
            'Associating PropertyStates across Cycles for %s.' % org.name,
            ending='\n'
        )

        properties = org.property_set.prefetch_related('views')
        partitioner = EquivalencePartitioner.make_default_state_equivalence(PropertyState)

        views = PropertyView.objects.none()
        for property in properties:
            views = views | property.views.all()

        matching_state_key_views = defaultdict(lambda: PropertyView.objects.none())
        for view in views:
            current_key = partitioner.calculate_comparison_key(view.state)

            # get matching_key if one exists, otherwise use current_key
            matching_key = next(
                (
                    existing_key
                    for existing_key
                    in matching_state_key_views.keys()
                    if partitioner.calculate_key_equivalence(existing_key, current_key)),
                current_key
            )

            matching_state_key_views[matching_key] = matching_state_key_views[matching_key] | PropertyView.objects.filter(id=view.id)

        pending_deletion = []
        for matches_qs in matching_state_key_views.values():
            match_ids = list(matches_qs.values('id', 'property_id', 'cycle_id', 'state_id'))# TODO: revisit this
            if matches_qs.count() < 2:
                continue
            else:
                matches = list(matches_qs)
                first_view = matches.pop(0)
                first_property = first_view.property

                # instantiate running QS of labels
                labels = first_property.labels.all()
                for view in matches:
                    # before updating view, update running labels QS
                    labels = labels | view.property.labels.all()

                    pending_deletion.append(view.property.id)
                    view.property = first_property
                    # view.save()

                    try:# TODO: revisit
                        view.save()
                    except:
                        import pdb; pdb.set_trace()

                # update property labels
                first_property.labels.set([l for l in labels])

        Property.objects.filter(id__in=pending_deletion).delete()  # Also deletes property_label records

        """
        ------------------
        Repeat for TaxLots
        ------------------
        """
        self.stdout.write(
            'Associating TaxLotStates across Cycles for %s.' % org.name,
            ending='\n'
        )
        partitioner = EquivalencePartitioner.make_default_state_equivalence(TaxLotState)
        taxlots = org.taxlot_set.prefetch_related('views')

        views = TaxLotView.objects.none()
        for taxlot in taxlots:
            views = views | taxlot.views.all()

        matching_state_key_views = defaultdict(list)
        for view in views:
            current_key = partitioner.calculate_comparison_key(view.state)

            # get matching_key if one exists, otherwise use current_key
            matching_key = next(
                (
                    existing_key
                    for existing_key
                    in matching_state_key_views.keys()
                    if partitioner.calculate_key_equivalence(existing_key, current_key)),
                current_key
            )

            matching_state_key_views[matching_key].append(view)

        pending_deletion = []
        for matches in matching_state_key_views.values():
            if len(matches) < 2:
                continue
            else:
                first_taxlot = matches.pop(0).taxlot

                # instantiate running QS of labels
                labels = first_taxlot.labels.all()
                for view in matches:
                    # before updating view, update running labels QS
                    labels = labels | view.taxlot.labels.all()

                    pending_deletion.append(view.taxlot.id)
                    view.taxlot = first_taxlot
                    view.save()

                # update property labels
                first_taxlot.labels.set([l for l in labels])

        TaxLot.objects.filter(id__in=pending_deletion).delete()  # Also deletes taxlot_label records

        self.stdout.write('Success!', ending='\n')
