import sys

sys.path.append('./instrClass')

from instrClass.baInstr import BaInstr


ba = BaInstr()

resp = b'E0101,MS_PRO=ABSTAND_ZU_GROSS,'

cks = ba.get_cksum(resp)
print(cks)
print(ba.parse_resp(b'E0101,MS_PRO=ABSTAND_ZU_GROSS,1C36'))