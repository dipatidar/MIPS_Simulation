
import sys
import os
from typing import Union
from enum import Enum

import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install("bitarray")

from bitarray import bitarray


class Dissembler:

    def __init__(self,file_path):
      self.file_path = file_path
      #self.read_file(file_path)
  
    
    def read_file(self, file_path:str):
      assert os.path.exists(file_path), "File does not exist at given location, "+str(file_path)
      self.inst_binary_dict = {}
      PC = 260
      with open(file_path,'r') as file:
        for line in file.readlines():
          #print(str(line).rstrip())
          self.inst_binary_dict[PC] = str(line).rstrip()
          PC = PC+4
      self.last_address = PC - 4
      self.mips_sim()


    cat_one_function_table = {}
    cat_one_function_table["000"] = {"operation":"J","style":0}
    cat_one_function_table["001"] = {"operation":"BEQ", "style":1}
    cat_one_function_table["010"] = {"operation":"BNE", "style":1}
    cat_one_function_table["011"] = {"operation":"BGTZ", "style":2}
    cat_one_function_table["100"] = {"operation":"SW", "style":3}
    cat_one_function_table["101"] = {"operation":"LW", "style":3}
    cat_one_function_table["110"] = {"operation":"BREAK", "style":4}


    cat_two_function_table = {}
    cat_two_function_table["000"] = {"operation":"ADD", "style":0}
    cat_two_function_table["001"] = {"operation":"SUB", "style":0}
    cat_two_function_table["010"] = {"operation":"AND", "style":0}
    cat_two_function_table["011"] = {"operation":"OR", "style":0}
    cat_two_function_table["100"] = {"operation":"SRL", "style":1}
    cat_two_function_table["101"] = {"operation":"SRA", "style":1}
    cat_two_function_table["110"] = {"operation":"MUL", "style":0}


    cat_three_function_table= {}
    cat_three_function_table["000"] = "ADDI"
    cat_three_function_table["001"] = "ANDI"
    cat_three_function_table["010"] = "ORI"
    
    class INSTRUCTION_CATEGORY(Enum):
      CATEGORY_ONE=1
      CATEGORY_TWO=2
      CATEGORY_THREE=3
      NONE_TYPE=-1
      
  

    def translate_to_assembly(self):
      PC = 260
      self.is_inst = True
      with open('sample_disassembly.txt', 'a') as assembly_file:
        for line in self.lines:
          binary_code= line
          output_instruction = ""
          if self.is_inst:
            least_most_bits = line[0:3]

            instruction_type = self.check_type(least_most_bits)
            if instruction_type ==self.INSTRUCTION_CATEGORY.CATEGORY_ONE:
                output_instruction, address = self.dissemble_cat_one(binary_code,PC)
                if "BREAK" in output_instruction:
                  self.is_inst = False
            elif instruction_type == self.INSTRUCTION_CATEGORY.CATEGORY_TWO:
                output_instruction, address = self.dissemble_cat_two(binary_code)
            elif instruction_type == self.INSTRUCTION_CATEGORY.CATEGORY_THREE:
                output_instruction, address= self.dissemble_cat_three(binary_code)
      
          else:

              output_instruction= self.binary_to_decimal_signed(binary_code)
         
          assembly_file.write(line + '\t' + str(PC) + '\t' + str(output_instruction)+'\n')
          PC += 4


    def check_type(self, least_most_bits: str)->Enum: 
      if least_most_bits=="000":
        return self.INSTRUCTION_CATEGORY.CATEGORY_ONE
      elif least_most_bits=="001":
        return self.INSTRUCTION_CATEGORY.CATEGORY_TWO
      elif least_most_bits=="010":
        return self.INSTRUCTION_CATEGORY.CATEGORY_THREE
      else:
        return self.INSTRUCTION_CATEGORY.NONE_TYPE


    def binary_to_decimal_unsigned(self, bin_str: str, n_bits:int = 32)->int:
      return int(bin_str,2)

    def binary_to_decimal_signed(self, bin_str: str, n_bits:int = 32)->int:
      sign = bin_str[0]
      if sign == '0':
          return int(bin_str,2)
      elif sign == '1':
          comp = int(bin_str[1:],2)
          dec = (2**(n_bits-1)) - comp
          return -1*dec

    def dec2bin(self,dec, n_bits):
      if int(dec) < 0:
          dec = int(dec)
          b = BitArray(int=dec,length=n_bits)
          return b.bin
      else:
          return bin(int(dec))[2:].zfill(n_bits)


    def simulate_cat_one(self,rd:int, rs:int, offset:int, operation:str, address:int, num_addr: int):
      if operation == "BEQ":
        if self.modified_register_values[rd] == self.modified_register_values[rs]:
          address= address+offset   
      elif operation == "BNE":
        if self.modified_register_values[rd] != self.modified_register_values[rs]:
          address= address+offset       
      elif operation == "BGTZ":
        if self.modified_register_values[rd]>0:
          address= address+offset
      elif operation == "SW":
        self.register_values[int((offset-num_addr+self.modified_register_values[rd])/4)] = int(self.modified_register_values[rs])

      elif operation == "LW":
        self.modified_register_values[rs] = int(self.register_values[int((offset - num_addr + self.modified_register_values[rd])/4)])

      return address

    def dissemble_cat_one(self, binary_value:str,PC:int,num_address:int, is_sim :bool = False)->Union [str,int]:
      inst = ""
      opcode = binary_value[3:6]
      address = PC
      #print(address)
      operation = self.cat_one_function_table[opcode]['operation']
      style = self.cat_one_function_table[opcode]['style']

      if style==4:
          inst=operation
      elif style==0:
        address = binary_value[6:]
        address = self.binary_to_decimal_unsigned(address,2) << 2
        address = self.dec2bin(PC,32)[0:4]+self.dec2bin(address,28)

        address = self.binary_to_decimal_unsigned(address)

        inst = operation + ' #' +str(address)
        
      else:

        rs = self.binary_to_decimal_unsigned(binary_value[6:11])
        rt = self.binary_to_decimal_unsigned(binary_value[11:16])
        offset = self.binary_to_decimal_unsigned(binary_value[16:],16)
        if style ==1:
          offset = offset*4
          inst =  operation + ' R' + str(rs) + ', R' + str(rt) + ', #' + str(offset)
        elif style==2:
          offset = offset*4
          inst = operation + ' R' + str(rs) + ', #' + str(offset)
        elif style==3:
          inst = operation + ' R' + str(rt) + ', ' + str(offset) + '(R' + str(rs) + ')'
        if is_sim:
          address = self.simulate_cat_one(rs,rt,offset,operation,address,num_address)
      return inst,address

    def simulate_cat_two(self,rd:int, rs:int, rt:int, operation:str):

      if operation == "ADD":
        self.modified_register_values[rd] = self.modified_register_values[rs] + self.modified_register_values[rt]
      elif operation == "SUB":
        self.modified_register_values[rd] = self.modified_register_values[rs] - self.modified_register_values[rt]
      elif operation == "MUL":
        self.modified_register_values[rd] =  self.modified_register_values[rs] * self.modified_register_values[rt]
      elif operation == "OR":
        self.modified_register_values[rd] =  self.modified_register_values[rs] | self.modified_register_values[rt]
      elif operation == "AND":
        self.modified_register_values[rd] = self.modified_register_values[rs] & self.modified_register_values[rt]
      elif operation == "SRL":

        self.modified_register_values[rd] = (self.modified_register_values[rs] % 0x100000000) >> rt
        
      elif operation == "SRA":

        self.modified_register_values[rd] =  self.modified_register_values[rs] >> rt



    def dissemble_cat_two(self, binary_value:str,is_sim:bool = False)->Union[str,int]:
      inst = ""
      opcode = binary_value[3:6]
      rd = self.binary_to_decimal_unsigned(binary_value[6:11])
      #print(rd)
      #print(binary_value[6:11])
      rs = self.binary_to_decimal_unsigned(binary_value[11:16])
      rt = self.binary_to_decimal_unsigned(binary_value[16:21])

      operation = self.cat_two_function_table[opcode]["operation"]
      style = self.cat_two_function_table[opcode]["style"]

      if style==0:
        inst = operation + ' R' + str(rd) + ', R' + str(rs) + ', R' + str(rt)
      elif style==1:
        inst = operation + ' R' +str(rd) + ', R' + str(rs) + ', #' +str(rt)

      if is_sim:
        self.simulate_cat_two(rd,rs,rt,operation)

      return inst, 0


    def simulate_cat_three(self,rd:int, rs:int, imm:int, operation:str):
      if operation == "ADDI":
        self.modified_register_values[rd] = self.modified_register_values[rs]+ imm
      elif operation == "ANDI":
        self.modified_register_values[rd] = self.modified_register_values[rs] & imm
      elif operation == "ORI":
        self.modified_register_values[rd] = self.modified_register_values[rs] | imm

    def dissemble_cat_three(self, binary_value:str, is_sim : bool = False)->Union[str,int]:
      inst = ""
      opcode = binary_value[3:6]
      rd = self.binary_to_decimal_unsigned(binary_value[6:11])
      rs = self.binary_to_decimal_unsigned(binary_value[11:16])
      imm = self.binary_to_decimal_signed(binary_value[16:],16)

      operation = self.cat_three_function_table[opcode]

      inst = operation + ' R' + str(rd) + ', R' + str(rs) + ', #' + str(imm)

      if is_sim:
          self.simulate_cat_three(rd,rs,imm, operation)

      return inst, 0
     
    def generate_sim_out_string(self, cycle:int, PC:int,inst:str, number_address:int)->str:
        
        #generate the "Registers" section

        reg_sec = "Registers\n"
        reg_sec += "R00:\t" + str(self.modified_register_values[0]) + "\t" + str(self.modified_register_values[1]) + "\t"+str(self.modified_register_values[2]) + "\t" +str(self.modified_register_values[3]) + "\t"+str(self.modified_register_values[4]) + "\t"+ str(self.modified_register_values[5]) + "\t"+str(self.modified_register_values[6])+"\t"+str(self.modified_register_values[7])+ "\n"
        reg_sec +="R08:\t" + str(self.modified_register_values[8]) + "\t" + str(self.modified_register_values[9]) + "\t"+str(self.modified_register_values[10]) + "\t" +str(self.modified_register_values[11]) + "\t"+str(self.modified_register_values[12]) + "\t"+ str(self.modified_register_values[13]) + "\t"+str(self.modified_register_values[14])+"\t"+str(self.modified_register_values[15])+ "\n"
        reg_sec +="R16:\t" + str(self.modified_register_values[16]) + "\t" + str(self.modified_register_values[17]) + "\t"+str(self.modified_register_values[18]) + "\t" +str(self.modified_register_values[19]) + "\t"+str(self.modified_register_values[20]) + "\t"+ str(self.modified_register_values[21]) + "\t"+str(self.modified_register_values[22])+"\t"+str(self.modified_register_values[23])+ "\n"
        reg_sec += "R24:\t" + str(self.modified_register_values[24]) + "\t" + str(self.modified_register_values[25]) + "\t"+str(self.modified_register_values[26]) + "\t" +str(self.modified_register_values[27]) + "\t"+str(self.modified_register_values[28]) + "\t"+ str(self.modified_register_values[29]) + "\t"+str(self.modified_register_values[30])+"\t"+str(self.modified_register_values[31])+ "\n\n"       
        
        #generate the "Data" section

        data_sec = "Data";
        memory_size = len(self.register_values)-1
        counter=0
   
        while (counter<=memory_size & memory_size>0):
          if counter%8 == 0:
            data_sec += "\n"+str(number_address+ counter*4)+":\t"
          if counter==memory_size:
            data_sec += str(self.register_values[counter])+"\n"
          else:
            data_sec += str(self.register_values[counter])+"\t"
          counter+=1
          
        sim_out_inst = "Cycle " +str(cycle)+":\t"+str(PC)+ "\t"+inst+"\n\n" 
        sim_out = "\n--------------------\n"+sim_out_inst+reg_sec+data_sec 

        return sim_out

    def mips_sim(self):
      PC = 260
      self.register_values  = []
      self.modified_register_values = []
      address_binary_dict = {}
      number_address = 0
      for i in range(0,32):
        self.modified_register_values.append(0)
      is_inst = True
      with open('disassembly.txt', 'w') as assembly_file:
        while PC <= self.last_address:
          binary_code= self.inst_binary_dict[PC]
          address_binary_dict[PC] = binary_code
          output_instruction = ""
          if is_inst:
            least_most_bits = binary_code[0:3]
           
            instruction_type = self.check_type(least_most_bits)

            if instruction_type ==self.INSTRUCTION_CATEGORY.CATEGORY_ONE:
                output_instruction, address = self.dissemble_cat_one(binary_code,PC,number_address)
      
                if "BREAK" in output_instruction:
                  is_inst = False
                  number_address = PC+4
                  ##print(self.is_inst)
            elif instruction_type == self.INSTRUCTION_CATEGORY.CATEGORY_TWO:
                output_instruction, address = self.dissemble_cat_two(binary_code)
            elif instruction_type == self.INSTRUCTION_CATEGORY.CATEGORY_THREE:
                output_instruction, address= self.dissemble_cat_three(binary_code)
      
          else:
              output_instruction= self.binary_to_decimal_signed(binary_code)
              self.register_values.append(output_instruction)
        
          assembly_file.write(binary_code + '\t' + str(PC) + '\t' + str(output_instruction)+'\n')
          PC += 4

        with open('simulation.txt', 'w') as simulation_file:
          cycle = 1
          PC = 260
  
          while PC <= self.last_address:
            binary_code= self.inst_binary_dict[PC]
            is_jump = False
            is_inst_break= False
            address=0
            output_instruction = ""
            least_most_bits = binary_code[0:3]

            instruction_type = self.check_type(least_most_bits)
            if instruction_type ==self.INSTRUCTION_CATEGORY.CATEGORY_ONE:
                output_instruction, address = self.dissemble_cat_one(binary_code,PC,number_address,True)
                if "BREAK" in output_instruction:
                  is_inst_break = True
                elif "J" in output_instruction:
                  is_jump=True
                  
            elif instruction_type == self.INSTRUCTION_CATEGORY.CATEGORY_TWO:
                output_instruction, address = self.dissemble_cat_two(binary_code,True)
            elif instruction_type == self.INSTRUCTION_CATEGORY.CATEGORY_THREE:
                output_instruction, address= self.dissemble_cat_three(binary_code, True)
              
 
            simulation_file.write(self.generate_sim_out_string(cycle, PC,output_instruction, number_address))
            if is_inst_break:
                break
            cycle+=1
            
            if address!=0:
              PC = address
            if not is_jump:
              PC += 4
      

if __name__=="__main__":
  
  input_file_name = sys.argv[1]
  dissembler = Dissembler(input_file_name)
  
  dissembler.read_file(input_file_name)

  