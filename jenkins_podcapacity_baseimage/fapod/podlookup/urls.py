from django.urls import path

# importing views from views..py
from .views import *

urlpatterns = [
    path('falookup/test', get_weekly_report, name = "test_page"),
    path('falookup/psranalysis', psr_analysis_report, name = "PSRAnalysis_Page"),
    #path('falookup/stamppage', stamp_manual_get_report, name = "stamp_page"),
    path('falookup/stamppage', get_weekly_report, name = "stamp_page"),
    path('falookup/index', index_page, name = "index_page"),
    path('falookup/podbasic', PodBasicData, name = "PodBasicDataPage"),
    path('falookup/exadatainfo', ExaDataFetchMethod, name = "ExaDataFetchMethodPage"),
    path('falookup/podinstance', PodInstanceData, name = "PodInstanceDataPage"),
    path('falookup/instdata', InstDataMethod, name = "InstData"),
    path('falookup/capview', CapViewMethod, name = "CapView"),
    path('falookup/capacityreservation', CapacityReservationMethod, name = "CapacityReservationPage"),
    #path('falookup/lbaas', lbaas_info_method, name = "lbaasmainpage"),
    path('falookup/lbaasdetails', lbaas_id_view_method, name = "LBaasIdView"),
    path('falookup/exadatadetails', ExaDataNodeViewMethod, name = "ExaDataNodeView"),
    #path('saasmon/capacity/', capacity_page_view, name = "capacity_page"),
    path('falookup/podcapacitydetails', test, name = "test_page_for_podcapacity"),
    path('falookup/podcapacitydashboard', CapacityReservationMethod, name = "PodCapacityDashboard_Page"),
    path('falookup/podcapacitydashboardmainpage', CapacityReservationMainMethod, name = "PodCapacityDashboard_MainPage"),
    path('falookup/podsizeanalyse', PodSizeAnalyseMethod, name = "PodSizeAnalyse_Page"),
    path('falookup/credstore_page', credstore_pageMethod, name = "credstore_page"),
    path('falookup/psrpagecap', psrpagecapviewMethod, name = "psrpagecapview"),
    #path('falookup/PodHostData', PodHostDataMethod, name = "PodHostDataUrl"),

]
