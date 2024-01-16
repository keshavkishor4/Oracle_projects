Please follow the below steps to encrypt oss password and create .passwd.json

1. get the rman_user password and pass as a parameter to following URL to generate encrypted password, use below curl URL
curl -sk --data "password=<bkup_oss_password from sre_db.cfg>" http://<catalog_db_URL>/crypto/encrypt | jq .

sample

2. create .passwd.json please refer to BASE_DIR/config/db/.passwd.json_sample
Sample below
{
    "oss_namespace<>" : {
        "rman_user"         : "",
        "fa_rman_oss_bn "   : "RMAN_BACKUP",
        "em_rman_user"      : "",
        "em_rman_oss_bn"    : "OMS_RMAN_BACKUP",
        "tenancy"           : "tenancy_name"
    }
}
3. uploaded to rman_wallet_bucket for that region.
4.Ensure config_oci.json is correct.

