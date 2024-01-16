faops tf services are an extension of FALCM services.
Confluence: https://confluence.oraclecorp.com/confluence/display/SPTA/FAOPS+Control+Plane
Directory Layout

                            <root dir>
                                |
                                |
                -----------------------------------         
                |          |          |           |
            resources   scripts   tfconfigs   tfmodules
                                      |
                              --------------------
                              |                  |
                            faops     <soft link to tenancy, eg: saasfaprod1 env file>
                              |
              ----------------------------------------------------------------------------------------------------------- ----------------------------- 

              |                       |                 |                         |                                     |                            |
    faops_psrtools_instances  faops_tf_buckets   faops_sopsvm_instances  faops_sopsutilvm_instances          faops_provutilvm_instances     faops_perftools_*  


1. faops_psrtools_instances - https://confluence.oraclecorp.com/confluence/display/SPTA/FAOPS+Control+Plane#FAOPSControlPlane-FAOPS_PSR_TOOLS-AllRegions 
  a. Update <tenancy env file> with following parameter , based on number of ADs, choose the right parameter
      # Three AD
      export TF_VAR_faops_psrtools_ad_indices=['0','1']
      # Single AD
      export TF_VAR_faops_psrtools_ad_indices=['0','0']

  b. Source the environment file
  c. create TF buckets
      - cd <root dir>/tfconfigs/faops/faops_tf_buckets
      - run terraform init, plan and apply
  d. create faops_psrtools_instances
      - cd <root dir>/tfconfigs/faops/faops_psrtools_instances
      - run terraform init, plan and apply
    #### S3 Backend

2. faops_sopsvm_instances - https://confluence.oraclecorp.com/confluence/display/SPTA/FAOPS+Control+Plane#FAOPSControlPlane-FAOPS_SOPSVM-FRAONLY
 a. To be executed in Production - FRA only & IAD only
 b. No change of variables required
 c. Set env variable/or put in env file=> TF_VAR_faops_sops_lb_shape="100Mbps" or desired shape
 d. Source the environment file
 e. create faops_sopsvm_instances
    - cd <root dir>/tfconfigs/faops/faops_sopsvm_instances
    - run terraform init, plan and apply
    <TODO: This section will need to be filled by the people who have set up this backend.>

3. faops_sopsutilvm_instances - https://confluence.oraclecorp.com/confluence/pages/viewpage.action?spaceKey=SPTA&title=FAOPS+Control+Plane#FAOPSControlPlane-FAOPS_SOPSVM_UTIL-FRA&IADONLY
 a. To be executed in Production - IAD only & PHX only
 b. No change of variables required
 c. Set env variable/or put in env file=> 
 TF_VAR_faops_sopsutilvm_lb_shape="100Mbps" or desired shape
 TF_VAR_faops_sopsutilvm_jenkins_hostname="saas-uptakecentral-stage-oci.<region>.falcm.ocs.oraclecloud.com"
 TF_VAR_faops_sopsutilvm_inv_hostname="saas-soe-apps-oci.<region>.falcm.ocs.oraclecloud.com"
    
 d. Source the environment file
 e. create faops_sopsvm_instances
    - cd <root dir>/tfconfigs/faops/faops_sopsutilvm_instances
    - run terraform init, plan and apply
    <TODO: This section will need to be filled by the people who have set up this backend.>
	
4. faops_provutilvm_instances - https://confluence.oraclecorp.com/confluence/display/SPTA/FAOPS+Control+Plane#FAOPSControlPlane-FAOPS_PROVUTILVM
 a. To be executed in Production - IAD only & PHX only
 b. No change of variables required
 c. Set env variable/or put in env file=> 
 TF_VAR_faops_provutilvm_lb_shape="100Mbps" or desired shape
 TF_VAR_faops_provutilvm_jenkins_hostname=saas-uptakecentral-prov-oci.<region>.falcm.ocs.oc-test.com
 TF_VAR_faops_provutilvm_inv_hostname= saas-prov-apps-stage-oci.<region>.falcm.ocs.oc-test.com

    
 d. Source the environment file
 e. create faops_provutilvm_instances
    - cd <root dir>/tfconfigs/faops/faops_provutilvm_instances
    - run terraform init, plan and apply
    <TODO: This section will need to be filled by the people who have set up this backend.>


5. faops_perftools_instance

 a. Update <tenancy env file> with following parameter , based on number of ADs, choose the right parameter
   i)
      # Three AD
      export TF_VAR_faops_psrtools_ad_indices=['0','1','2']
      # Single AD
      export TF_VAR_faops_psrtools_ad_indices=['0','0','0']
   ii)
     #Set lbaas shape -> change for PROD
      export TF_VAR_faops_perftools_lb_shape="100Mbps"   
     #For Prod
      export TF_VAR_faops_perftools_lb_shape="400Mbps"
  b. Source the environment file
  c. create faops_perftools_instances
      - cd <root dir>/tfconfigs/faops/faops_psrtools_instances
      - run terraform init, plan and apply

5. faops_perftools_db
  a. Source the environment file
  b. create faops_perftools_db
      - cd <root dir>/tfconfigs/faops/faops_psrtools_instances
      - run terraform init, plan and apply

    See [this blog](https://medium.com/oracledevs/storing-terraform-remote-state-to-oracle-cloud-infrastructure-object-storage-b32fe7402781) for general info about this approach.

6. faops_catalogdb_docker - update MAY-2022
===

7. faops_catalogdb_19c :- (https://confluence.oraclecorp.com/confluence/display/SPTA/FAOPS+Control+Plane#FAOPSControlPlane-FAOPS_CATALOGDB_19C)
  a. Source the environment file
  b. Create faops_catalogdb_19c
    - cd <root dir>/tfconfigs/faops/faops_catalogdb-19c
    - run terraform init, plan and apply

8. faops_catalogdb_mig:- (https://confluence.oraclecorp.com/confluence/display/SPTA/FAOPS+Control+Plane#FAOPSControlPlane-FAOPS_CATALOGDB_MIG)
  a. Source the environment file
  b. Create faops_catalogdb_mig
    - cd <root dir>/tfconfigs/faops/faops_catalogdb_mig
    - run terraform init, plan and apply
