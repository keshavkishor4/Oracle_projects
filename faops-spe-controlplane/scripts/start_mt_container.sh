#!/bin/bash
containerIDs="faopscbapi"
statusLived="live"
statusdead="Dead"
notExistContainer="None"
retryCount=3
function GetContainerStatus(){
 containerExist=$(docker ps -a | grep -i $1 | wc -l ) 
 if [ ${containerExist} -gt 0 ]
  then
  pid=$(docker stats --format "{{.PIDs}}" --no-stream $1 )
  if [ "${pid}" != "0" ]
   then 
   echo "${statusLived}"
  else
   echo "${statusdead}"
  fi
 else
  echo "${notExistContainer}" 
 fi
}
function StartContainer(){
 docker restart $1
}
for containerID in ${containerIDs}
 do
 for((i=1;i<=${retryCount};i++))
 do
 status=$(GetContainerStatus ${containerID} )
 echo "Container ${containerID} status is ${status}"
 if [ "${status}" == ${statusLived} ]
  then
  echo "Container ${containerID} already running"
  break
 fi
 if [ "${status}" == ${notExistContainer} ]
  then
  echo "Container ${containerID} not existed"
  break
 fi
 if [ "${status}" == ${statusdead} ]
  then
  echo "Container ${containerID} stopped ,start container"
  StartContainer ${containerID}
  verifyStatus=$(GetContainerStatus ${containerID} )
  if [ "${verifyStatus}" == ${statusLived} ]
   then
    echo "start container ${containerID} success "
    break
  else
   echo "${i} retry start container"
   StartContainer ${containerID}
  fi
 fi
 done
done
