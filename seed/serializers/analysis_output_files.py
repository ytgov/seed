# !/usr/bin/env python
# encoding: utf-8
"""
:copyright (c) 2014 - 2020, The Regents of the University of California, through Lawrence Berkeley National Laboratory (subject to receipt of any required approvals from the U.S. Department of Energy) and contributors. All rights reserved.  # NOQA
:author
"""
from rest_framework import serializers

from seed.models import AnalysisOutputFile


class AnalysisOutputFileSerializer(serializers.ModelSerializer):
    content_type = serializers.SerializerMethodField('get_readable_content_type')

    class Meta:
        model = AnalysisOutputFile
        fields = '__all__'

    def get_readable_content_type(self, obj):
        return AnalysisOutputFile.CONTENT_TYPES[next((i for i, v in enumerate(AnalysisOutputFile.CONTENT_TYPES) if v[0] == obj.content_type), None)][1]