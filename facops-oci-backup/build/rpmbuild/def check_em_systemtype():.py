def check_em_systemtype():
    try:
        if "emdb" in globalvariables.LOCAL_HOST.split(".")[1].lower() :
            return True
        else:
            return False
    except Exception as e:
        message = "could not check em systemtype -> {0}".format(e)
        apscom.warn(message)
        
def check_dbaas_systemtype():
    try:
        if ("Exa" in instance_metadata.ins_metadata().dbSystemShape):
            return False
        else:
            return True
    except Exception as e:
        message = "could not check em systemtype -> {0}".format(e)
        apscom.warn(message)
        return None
