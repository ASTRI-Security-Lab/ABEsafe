import wx.lib.delayedresult as DR
import os
import sys
import re
from ctypes import *

class CPABE:
    """
        Declarations of ABEsafe system environment variables
        - The path of the key is exposed here and shall be protected by the user his own,
        it should be secure unless the user intentionally share the key to others outside
        this system

        Encryption, decryption, and validation methods are defined
        - Currently, the methods are executed through system call. It would be unsecure
        only if this code has been modified and ABEsafe is executed with administrator
        privilege.
    """
    ENC,DEC,OPEN,MKEY,CISPEC,POK = range(6)
    TMP = '/private/tmp/org.astri.cpabe'
    SHARED_FOLDER_NAME = ""
    HOME_PATH = ""
    SHARED_FOLDER_PATH = ""
    ABEsafe_PATH = SHARED_FOLDER_PATH+"/ABEsafe"
    KEYS_PATH = ".keys/"
    CONFIG_PATH = ABEsafe_PATH+"/.configs/"
    IMG_PATH = ABEsafe_PATH+"/userImages/"
    DATABASE_file = "test.db"
    DATABASE = CONFIG_PATH+DATABASE_file
    libc = CDLL("libabe.so")
    
    @staticmethod
    def runcpabe(runtype,jid,onresult,*args):
        """
            Environment variables exposed to all other modules,
            including the home path, shared folder path and name,
            key path, ABEsafe configuration path, and the database file
        """
        if runtype==CPABE.ENC:
            fcreate = args[0]
            f_seg2 = fcreate.rpartition('.')
            f_seg = f_seg2[0].rpartition('.')
            fcheck = fcreate
            replica = 1
            while os.path.exists(fcheck) and replica<=sys.maxint:
                fcheck = f_seg[0]+"("+str(replica)+")"+f_seg[1]+f_seg[2]+f_seg2[1]+f_seg2[2]
                replica += 1
            import tempfile
            ftmp = tempfile.NamedTemporaryFile()
            result = CPABE.libc.abe_encrypt(str(ftmp.name), str(CPABE.CONFIG_PATH+".pub_key"), str(args[1]), str(args[2].replace(';','')))
            DR.startWorker(onresult,CPABE.execbg,cargs=(ftmp,fcheck),wargs=(result,),jobID=jid)
        elif runtype==CPABE.DEC:
            result = CPABE.libc.abe_decrypt(str(args[0]), str(CPABE.CONFIG_PATH+".pub_key"), str("%s%s"%(CPABE.KEYS_PATH,args[1])), str(args[2].replace(';','')))
            DR.startWorker(onresult,CPABE.execbg,wargs=(result,),jobID=jid)
        elif runtype==CPABE.OPEN:
            status = CPABE.libc.abe_checkopen(str(CPABE.CONFIG_PATH+".pub_key"), str("%s%s"%(CPABE.KEYS_PATH,args[0])), str(args[1].replace(';','')))
            return status
        elif runtype==CPABE.MKEY:
            result = CPABE.libc.abe_checkmetapriv(str(CPABE.CONFIG_PATH+".pub_key"), str(args[0]), str("%s%s"%(CPABE.KEYS_PATH,args[1]).replace(';','')))
            DR.startWorker(onresult,CPABE.execbg,wargs=(result,),jobID=jid)
        elif runtype==CPABE.POK:
            if re.sub(r"\s+", '', args[0]) == "":
                return 1
            status = CPABE.libc.abe_checkmeta(str(CPABE.CONFIG_PATH+".pub_key"), str(args[0].replace(';','')))
            return status
    
    @staticmethod
    def execbg(result):
        return result
