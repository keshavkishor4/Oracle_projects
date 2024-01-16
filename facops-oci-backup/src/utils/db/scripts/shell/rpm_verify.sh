#!/bin/bash
region=$(curl -sL -k -X -H "Authorization: Bearer Oracle" GET http://169.254.169.254/opc/v2/instance/canonicalRegionName)
function postStatus(){
   #
   out=$(grep -i fa-spe-oci-backup-mt /var/log/messages | grep -i yum | tail -1)
   STATUS=$1
   output=$out
   HOST=$(hostname -f)
   RPM_VER=$(rpm -qa | grep -m 1 -i backup | uniq)
   CREATED=$(date '+%Y-%m-%d %H:%M:%S')
   IMAGE_REL=""
   OCID=$(curl -sL -k -X -H "Authorization: Bearer Oracle" GET http://169.254.169.254/opc/v2/instance/id)
   checkExa=$(curl --connect-timeout 10 -sL -H "Authorization: Bearer Oracle" http://169.254.169.254/opc/v2/instance/metadata/dbSystemShape 2>/dev/null)
   if [[ "${checkExa}" =~ "Exa" ]];then
      IMAGE_REL=$(imageinfo -ver)
   else
      IMAGE_REL=$(cat /etc/image-creation-release)
   fi
   
   # 
   json_file="/tmp/postrpminstall.json"
   cat >"$json_file" <<EOF
{
  "data": {
        "host"     : "${HOST}",
        "rpmver"   : "${RPM_VER}",
        "image_rel": "${IMAGE_REL}",
        "created": "${CREATED}",
        "status"    : "${STATUS}",
        "region"    : "${region}",
        "ocid"    : "${OCID}",
        "output" : "${output}"
    
    }   
}
EOF

# Post status
   rm -f $json_file

}

out=$(grep -i fa-spe-oci-backup-mt /var/log/messages | grep -i yum | tail -1)
if [[ -z $out ]];then
    status="FAILED"
    output="No entry found /var/log/messages"
    postStatus $status $output
else
    RESULT=$(echo $out | egrep 'Installed|Updated' > /dev/null 2>&1)
    if [[ $? -eq 0 ]];then
        echo "posting rpm status" | tee -a /tmp/backup_status.log
        status="SUCCESS"
        output=$out
        postStatus $status $output
        
    else
        echo "posting rpm status" | tee -a /tmp/backup_status.log
        status="FAILED"
        output="No entry found /var/log/messages"
        postStatus $status $output
    fi
fi

