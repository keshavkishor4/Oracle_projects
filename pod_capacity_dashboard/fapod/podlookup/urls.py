from django.urls import re_path

# importing views from views..py
from .views import *

urlpatterns = [
    re_path('falookup/test', get_weekly_report, name = "test_page"),
    re_path('falookup/psranalysis', psr_analysis_report, name = "PSRAnalysis_Page"),
    #re_path('falookup/stamppage', stamp_manual_get_report, name = "stamp_page"),
    re_path('falookup/stamppage', get_weekly_report, name = "stamp_page"),
    re_path('falookup/index', index_page, name = "index_page"),
    re_path('falookup/podbasic', PodBasicData, name = "PodBasicDataPage"),
    re_path('falookup/exadatainfo', ExaDataFetchMethod, name = "ExaDataFetchMethodPage"),
    re_path('falookup/dbinitconf', DBInitConfiguration, name = "DBInitConfiguration"),
    re_path('falookup/heapsize', ComputeDataMethod, name = "ComputeDataMethod"),
    re_path('falookup/podinstance', PodInstanceData, name = "PodInstanceDataPage"),
    re_path('falookup/instdata', InstDataMethod, name = "InstData"),
    re_path('falookup/podfamily', PodFamilyViewMethod, name = "PodFamilyView"),
    re_path('falookup/bespokedetails', bespoke_data, name = "BespokeDetails"),
    re_path('falookup/bespokedbdetails', bespoke_db_data, name = "BespokeDBDetails"),
    re_path('falookup/capview', CapViewMethod, name = "CapView"),
    re_path('falookup/capacityreservation', CapacityReservationMethod, name = "CapacityReservationPage"),
    #re_path('falookup/lbaas', lbaas_info_method, name = "lbaasmainpage"),
    re_path('falookup/lbaasdetails', lbaas_id_view_method, name = "LBaasIdView"),
    re_path('falookup/exadatadetails', ExaDataNodeViewMethod, name = "ExaDataNodeView"),
    re_path('falookup/homepodinstdata', HomePodDataDetails, name = "InstanceDataView"),
    re_path('falookup/ocisessauth', ocisessauthmethod, name = "ocisessauth"),
    #re_path('saasmon/capacity/', capacity_page_view, name = "capacity_page"),
    re_path('falookup/podcapacitydetails', test, name = "test_page_for_podcapacity"),
    re_path('falookup/podcapacitydashboard', CapacityReservationMethod, name = "PodCapacityDashboard_Page"),
    re_path('falookup/podcapacitydashboardmainpage', CapacityReservationMainMethod, name = "PodCapacityDashboard_MainPage"),
    re_path('falookup/podsizeanalyse', PodSizeAnalyseMethod, name = "PodSizeAnalyse_Page"),
    re_path('falookup/credstore_page', credstore_pageMethod, name = "credstore_page"),
    re_path('falookup/psrpagecap', psrpagecapviewMethod, name = "psrpagecapview"),
    re_path('falookup/faascapdetails', faascapdetailsMethod, name = "faascapdetails"),
    re_path('falookup/faasdbdata', faasdbMethod, name = "faasdbdetails"),
    re_path('falookup/faasexadata', faasexadataMethod, name = "Faasexadata"),
    #re_path('falookup/PodHostData', PodHostDataMethod, name = "PodHostDataUrl"),

]
