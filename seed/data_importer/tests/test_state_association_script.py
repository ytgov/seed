# !/usr/bin/env python
# encoding: utf-8
import datetime

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone as tz

from io import StringIO

from seed.landing.models import SEEDUser as User
from seed.models import (
    Cycle,
    Property,
    PropertyState,
    PropertyView,
    TaxLot,
    TaxLotState,
    TaxLotView,
)
from seed.test_helpers.fake import (
    FakePropertyFactory,
    FakePropertyStateFactory,
    FakePropertyViewFactory,
    FakeTaxLotFactory,
    FakeTaxLotStateFactory,
    FakeTaxLotViewFactory,
)
from seed.utils.organizations import create_organization


class StateAssociationTests(TestCase):
    def test_state_association_doesnt_do_anything_if_invalid_org_name_provided(self):
        out = StringIO()
        call_command('associate_states_across_cycles', "--organization=some organization", stdout=out)
        self.assertIn('some organization is not an existing Organization.', out.getvalue())

    def test_state_association_script_specifying_org_by_name(self):
        """
        This test verifies Property/TaxLot -States representing the same
        property/taxlot across different Cycles are associated appropriately.
        Since this requires setting up different scenarios where the
        associations were not set up previously, the setup for this is fairly
        long.

        Specifically, it needs to be verified -Views have been
        disassociated and reassociated appropriately once this script is run.

        The following will be created:
            - 1 Org
            - 1 User
            - 3 Cycles - 2016, 2017, 2018
                - 8 Property and 8 PropertyView
                    - 3, 3, 2 split across cycles respectively
                - 8 TaxLot and 8 TaxLotView
                    - 3, 3, 2 split across cycles respectively

            Properties:
            - 2 to be associated PropertyStates
            - 3 separate to be associated PropertyStates
            - 3 PropertyStates with no associations (singles)

            TaxLots:
            - 2 to be associated TaxLotStates
            - 3 separate to be associated TaxLotStates
            - 3 TaxLotStates with no associations (singles)

        Once associations are made, the orphaned Properties/TaxLots will be deleted.
        """
        # Create User
        user_details = {
            'username': 'test_user@demo.com',
            'password': 'test_pass',
        }
        user = User.objects.create_superuser(
            email='test_user@demo.com', **user_details
        )

        # Create Org
        org, _, _ = create_organization(user, org_name='Test Organization')

        # Create Cycles
        cycle_2016, _ = Cycle.objects.get_or_create(
            name='Test Hack Cycle 2016',
            organization=org,
            start=datetime.datetime(2016, 1, 1, tzinfo=tz.get_current_timezone()),
            end=datetime.datetime(2016, 12, 31, tzinfo=tz.get_current_timezone()),
        )
        cycle_2017, _ = Cycle.objects.get_or_create(
            name='Test Hack Cycle 2017',
            organization=org,
            start=datetime.datetime(2017, 1, 1, tzinfo=tz.get_current_timezone()),
            end=datetime.datetime(2017, 12, 31, tzinfo=tz.get_current_timezone()),
        )
        cycle_2018, _ = Cycle.objects.get_or_create(
            name='Test Hack Cycle 2018',
            organization=org,
            start=datetime.datetime(2018, 1, 1, tzinfo=tz.get_current_timezone()),
            end=datetime.datetime(2018, 12, 31, tzinfo=tz.get_current_timezone()),
        )

        # Create Factories for Property, PropertyState, and PropertyView
        p_factory = FakePropertyFactory(organization=org)
        p_state_factory = FakePropertyStateFactory(organization=org)
        p_view_2016_factory = FakePropertyViewFactory(organization=org, cycle=cycle_2016)
        p_view_2017_factory = FakePropertyViewFactory(organization=org, cycle=cycle_2017)
        p_view_2018_factory = FakePropertyViewFactory(organization=org, cycle=cycle_2018)

        # Create Factories for TaxLot, TaxLotState, and TaxLotView
        tl_factory = FakeTaxLotFactory(organization=org)
        tl_state_factory = FakeTaxLotStateFactory(organization=org)
        tl_view_2016_factory = FakeTaxLotViewFactory(organization=org, cycle=cycle_2016)
        tl_view_2017_factory = FakeTaxLotViewFactory(organization=org, cycle=cycle_2017)
        tl_view_2018_factory = FakeTaxLotViewFactory(organization=org, cycle=cycle_2018)

        # Create Properties, PropertyStates, and PropertyViews
        # Create Properties
        property_1 = p_factory.get_property()
        property_2 = p_factory.get_property()
        property_3 = p_factory.get_property()
        property_4 = p_factory.get_property()
        property_5 = p_factory.get_property()
        property_6 = p_factory.get_property()
        property_7 = p_factory.get_property()
        property_8 = p_factory.get_property()

        # Create to-be-associated PropertyStates - Group 1
        p_state_1 = p_state_factory.get_property_state(address_line_1='123 Fake Street')
        p_state_2 = p_state_factory.get_property_state(address_line_1='123 Fake Street')

        # Create to-be-associated PropertyStates - Group 2
        p_state_3 = p_state_factory.get_property_state(address_line_1='123 Real Street')
        p_state_4 = p_state_factory.get_property_state(address_line_1='123 Real Street')
        p_state_5 = p_state_factory.get_property_state(address_line_1='123 Real Street')

        # Create remaining, unassociated PropertyStates
        p_state_6 = p_state_factory.get_property_state(address_line_1='1 Unassociated Street')
        p_state_7 = p_state_factory.get_property_state(address_line_1='2 Unassociated Street')
        p_state_8 = p_state_factory.get_property_state(address_line_1='3 Unassociated Street')

        # Create PropertyViews while connecting Properties with PropertyStates
        # Group 1 - Cycles 2016 and 2017
        p_view_2016_factory.get_property_view(prprty=property_1, state=p_state_1)
        p_view_2017_factory.get_property_view(prprty=property_2, state=p_state_2)

        # Group 2 - Cycles 2016, 2017, and 2018
        p_view_2016_factory.get_property_view(prprty=property_3, state=p_state_3)

        p_view_2017_factory.get_property_view(prprty=property_4, state=p_state_4)

        p_view_2018_factory.get_property_view(prprty=property_5, state=p_state_5)

        # Singles - Cycles 2016, 2017, and 2018
        p_view_2016_factory.get_property_view(prprty=property_6, state=p_state_6)
        p_view_2017_factory.get_property_view(prprty=property_7, state=p_state_7)
        p_view_2018_factory.get_property_view(prprty=property_8, state=p_state_8)

        # Create TaxLots, TaxLotsStates, and TaxLotsViews
        # Create TaxLots
        taxlot_1 = tl_factory.get_taxlot()
        taxlot_2 = tl_factory.get_taxlot()
        taxlot_3 = tl_factory.get_taxlot()
        taxlot_4 = tl_factory.get_taxlot()
        taxlot_5 = tl_factory.get_taxlot()
        taxlot_6 = tl_factory.get_taxlot()
        taxlot_7 = tl_factory.get_taxlot()
        taxlot_8 = tl_factory.get_taxlot()

        # Create to-be-associated TaxLotStates - Group 1
        tl_state_1 = tl_state_factory.get_taxlot_state(jurisdiction_tax_lot_id='100')
        tl_state_2 = tl_state_factory.get_taxlot_state(jurisdiction_tax_lot_id='100')

        # Create to-be-associated TaxLotStates - Group 2
        tl_state_3 = tl_state_factory.get_taxlot_state(jurisdiction_tax_lot_id='200')
        tl_state_4 = tl_state_factory.get_taxlot_state(jurisdiction_tax_lot_id='200')
        tl_state_5 = tl_state_factory.get_taxlot_state(jurisdiction_tax_lot_id='200')

        # Create remaining, unassociated TaxLotStates
        tl_state_6 = tl_state_factory.get_taxlot_state(jurisdiction_tax_lot_id='1')
        tl_state_7 = tl_state_factory.get_taxlot_state(jurisdiction_tax_lot_id='2')
        tl_state_8 = tl_state_factory.get_taxlot_state(jurisdiction_tax_lot_id='3')

        # Create TaxLotViews while connecting TaxLots with TaxLotStates
        # Group 1 - Cycles 2016 and 2017
        tl_view_2016_factory.get_taxlot_view(taxlot=taxlot_1, state=tl_state_1)
        tl_view_2017_factory.get_taxlot_view(taxlot=taxlot_2, state=tl_state_2)
        # Group 2 - Cycles 2016, 2017, and 2018
        tl_view_2016_factory.get_taxlot_view(taxlot=taxlot_3, state=tl_state_3)

        tl_view_2017_factory.get_taxlot_view(taxlot=taxlot_4, state=tl_state_4)

        tl_view_2018_factory.get_taxlot_view(taxlot=taxlot_5, state=tl_state_5)

        # Singles - Cycles 2016, 2017, and 2018
        tl_view_2016_factory.get_taxlot_view(taxlot=taxlot_6, state=tl_state_6)
        tl_view_2017_factory.get_taxlot_view(taxlot=taxlot_7, state=tl_state_7)
        tl_view_2018_factory.get_taxlot_view(taxlot=taxlot_8, state=tl_state_8)

        # Double-check setup
        # 8 Properties each associated to 1 PropertyState via PropertyView spread out across 3 Cycles
        self.assertEqual(Property.objects.count(), 8)
        for p in Property.objects.all():
            state_associations = p.views.select_related('state').values('state__id').count()
            self.assertEqual(state_associations, 1)

        self.assertEqual(cycle_2016.propertyview_set.count(), 3)
        self.assertEqual(cycle_2017.propertyview_set.count(), 3)
        self.assertEqual(cycle_2018.propertyview_set.count(), 2)

        # 8 TaxLots each associated to 1 TaxLotState via TaxLotView spread out across 3 Cycles
        self.assertEqual(TaxLot.objects.count(), 8)
        for tl in TaxLot.objects.all():
            state_associations = tl.views.select_related('state').values('state__id').count()
            self.assertEqual(state_associations, 1)

        self.assertEqual(cycle_2016.taxlotview_set.count(), 3)
        self.assertEqual(cycle_2017.taxlotview_set.count(), 3)
        self.assertEqual(cycle_2018.taxlotview_set.count(), 2)

        """
        ----------------------------
        Run State Association Script
        ----------------------------
        """
        # capture stdout
        out = StringIO()
        call_command('associate_states_across_cycles', "--organization=Test Organization", stdout=out)

        # Verify script worked as expected
        # General counts
        self.assertEqual(Property.objects.count(), 5)
        self.assertEqual(PropertyState.objects.count(), 8)
        self.assertEqual(PropertyView.objects.count(), 8)

        self.assertEqual(TaxLot.objects.count(), 5)
        self.assertEqual(TaxLotState.objects.count(), 8)
        self.assertEqual(TaxLotView.objects.count(), 8)

        # The same number of -Views should exist per Cycle as those records were reused.
        # None of these should have been deleted, nor should any have been created.
        self.assertEqual(cycle_2016.propertyview_set.count(), 3)
        self.assertEqual(cycle_2017.propertyview_set.count(), 3)
        self.assertEqual(cycle_2018.propertyview_set.count(), 2)

        self.assertEqual(cycle_2016.taxlotview_set.count(), 3)
        self.assertEqual(cycle_2017.taxlotview_set.count(), 3)
        self.assertEqual(cycle_2018.taxlotview_set.count(), 2)

        # Starting with Property objects, check PropertyState associations
        property_1_states = [state['state_id'] for state in property_1.views.select_related('state').values('state_id')]
        self.assertEqual(property_1_states, [p_state_1.pk, p_state_2.pk])
        property_2_states = [state['state_id'] for state in property_2.views.select_related('state').values('state_id')]
        self.assertEqual(property_2_states, [])

        property_3_states = [state['state_id'] for state in property_3.views.select_related('state').values('state_id')]
        self.assertEqual(property_3_states, [p_state_3.pk, p_state_4.pk, p_state_5.pk])

        property_4_states = [state['state_id'] for state in property_4.views.select_related('state').values('state_id')]
        self.assertEqual(property_4_states, [])
        property_5_states = [state['state_id'] for state in property_5.views.select_related('state').values('state_id')]
        self.assertEqual(property_5_states, [])
        property_6_states = [state['state_id'] for state in property_6.views.select_related('state').values('state_id')]
        self.assertEqual(property_6_states, [p_state_6.pk])
        property_7_states = [state['state_id'] for state in property_7.views.select_related('state').values('state_id')]
        self.assertEqual(property_7_states, [p_state_7.pk])
        property_8_states = [state['state_id'] for state in property_8.views.select_related('state').values('state_id')]
        self.assertEqual(property_8_states, [p_state_8.pk])

        # Starting with TaxLot objects, check TaxLotState associations
        taxlot_1_states = [state['state_id'] for state in taxlot_1.views.select_related('state').values('state_id')]
        self.assertEqual(taxlot_1_states, [tl_state_1.pk, tl_state_2.pk])
        taxlot_2_states = [state['state_id'] for state in taxlot_2.views.select_related('state').values('state_id')]
        self.assertEqual(taxlot_2_states, [])

        taxlot_3_states = [state['state_id'] for state in taxlot_3.views.select_related('state').values('state_id')]
        self.assertEqual(taxlot_3_states, [tl_state_3.pk, tl_state_4.pk, tl_state_5.pk])

        taxlot_4_states = [state['state_id'] for state in taxlot_4.views.select_related('state').values('state_id')]
        self.assertEqual(taxlot_4_states, [])
        taxlot_5_states = [state['state_id'] for state in taxlot_5.views.select_related('state').values('state_id')]
        self.assertEqual(taxlot_5_states, [])
        taxlot_6_states = [state['state_id'] for state in taxlot_6.views.select_related('state').values('state_id')]
        self.assertEqual(taxlot_6_states, [tl_state_6.pk])
        taxlot_7_states = [state['state_id'] for state in taxlot_7.views.select_related('state').values('state_id')]
        self.assertEqual(taxlot_7_states, [tl_state_7.pk])
        taxlot_8_states = [state['state_id'] for state in taxlot_8.views.select_related('state').values('state_id')]
        self.assertEqual(taxlot_8_states, [tl_state_8.pk])
