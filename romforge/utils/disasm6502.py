OPS={
0x00:("BRK","imp",1),0x20:("JSR","abs",3),0x40:("RTI","imp",1),0x4C:("JMP","abs",3),0x60:("RTS","imp",1),0x6C:("JMP","ind",3),
0x78:("SEI","imp",1),0x58:("CLI","imp",1),0xEA:("NOP","imp",1),0xA9:("LDA","imm",2),0xA2:("LDX","imm",2),0xA0:("LDY","imm",2),
0xAD:("LDA","abs",3),0xBD:("LDA","absx",3),0xB9:("LDA","absy",3),0x8D:("STA","abs",3),0x9D:("STA","absx",3),0x99:("STA","absy",3),
0x85:("STA","zp",2),0xA5:("LDA","zp",2),0xE8:("INX","imp",1),0xC8:("INY","imp",1),0xCA:("DEX","imp",1),0x88:("DEY","imp",1),
0xD0:("BNE","rel",2),0xF0:("BEQ","rel",2),0x10:("BPL","rel",2),0x30:("BMI","rel",2),0x90:("BCC","rel",2),0xB0:("BCS","rel",2),
0x29:("AND","imm",2),0x09:("ORA","imm",2),0x49:("EOR","imm",2),0x69:("ADC","imm",2),0xE9:("SBC","imm",2),0xC9:("CMP","imm",2)}
def disassemble(data,start):
 out=[]; i=0
 while i<len(data):
  a=(start+i)&0xffff; op=data[i]
  if op not in OPS: out.append(f"${a:04X}: {op:02X}        .db ${op:02X}"); i+=1; continue
  m,mode,n=OPS[op]
  if i+n>len(data): out.append(f"${a:04X}: {op:02X}        .db ${op:02X}"); i+=1; continue
  bs=data[i:i+n]; o=""
  if n==2:
   v=bs[1]
   if mode=="imm": o=f"#$%02X"%v
   elif mode=="zp": o=f"$%02X"%v
   elif mode=="rel":
    r=v if v<128 else v-256; o=f"${(a+2+r)&0xffff:04X}"
  elif n==3:
   v=bs[1]|bs[2]<<8; o={"abs":f"${v:04X}","absx":f"${v:04X},X","absy":f"${v:04X},Y","ind":f"(${v:04X})"}.get(mode,"")
  out.append(f"${a:04X}: {' '.join(f'{x:02X}' for x in bs).ljust(9)} {m} {o}".rstrip()); i+=n
 return out
