"""
All the public functions (those that don't start with _) defined here return the bytecode
for the named bus command.
"""
import os, os.path
import struct
import sys

from Exceptions import *

def _get_bytecode_info():
    bytecode_info_fname = os.path.join(os.path.dirname(__file__),
                                       "bytecode.info")
    NS = {}
    execfile(bytecode_info_fname,NS)
    return NS["bytecode_map"],NS["bytecode_signature"],NS["max_comment_size"]

(bytecode_command,bytecode_signature,max_comment_size) = _get_bytecode_info()


def signature():
    sig_size = len(bytecode_signature)
    bcode = struct.pack("=B",sig_size)
    bcode += struct.pack("=%dB" % sig_size,*(ord(c) for c in bytecode_signature))
    return (bcode,0)

def wait(cycles):
    cycles = int(cycles)
    bcode = struct.pack("=BQ",
                        bytecode_command["WAIT"],cycles)
    return (bcode,cycles)

def set_sampling_rate_divider(value):
    bcode = struct.pack("=BQ",
                        bytecode_command["SET_SAMPLING_RATE_DIVIDER"],value)
    return bcode

def comment(msg):
    assert max_comment_size == 1 << 8

    l = len(msg)
    if l > max_comment_size:
        raise Error("comment too long")

    bcode = struct.pack("=BB%ds" % l,
                        bytecode_command["COMMENT"],l,msg)
    return (bcode,0)
    
def raw_command(address,data,strobe):
    s = strobe != 0
    bcode = struct.pack("=BBHB",
                        bytecode_command["RAW"],address,data,s)
    return (bcode,1)

def simple_command(address,data):
    bcode = struct.pack("=BBH",
                        bytecode_command["COMMAND"],address,data)
    return (bcode,3)

def command_sequence(address,data):
    size = len(data)
    bcode = struct.pack("=BBQ",
                        bytecode_command["COMMAND_SEQUENCE"],
                        address,size)
    bcode += struct.pack("=%dH" % size,*data)
    return (bcode,3*size)

def stop():
    bcode = struct.pack("=B",bytecode_command["STOP"])
    return (bcode,0)
