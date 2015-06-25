import hashlib
import os
import subprocess
import proto.apk_analysis_pb2 as evalpb


"""
CONSTANTS
"""
GPL_STRING = "GPL"
HASHDEEP_SUFFIX = ".hashdeep"

"""
Utilities for app processing
"""
def unpack(infile):
	""" unpack the file 
	@parameter
	infile: zip or apk file
	@return
	unpack: the output directory
	"""
	apk_suffix = ".apk"
	zip_suffix = ".zip"
	if infile.endswith(apk_suffix):
		unpack = infile[:-4]
		p1 = subprocess.Popen(["apktool", "d", infile, "-o", unpack],
				stdout=subprocess.PIPE)
		output, error = p1.communicate()
	elif infile.endswith(zip_suffix):
		unpack = infile[:-4]
		p1 = subprocess.Popen(["unzip", infile, "-d", unpack],
				stdout=subprocess.PIPE)
		output, error = p1.communicate()
	else:
		raise Exception("Unhandled file extension")
	return unpack

def digest(infile, outfile=None):
	"""
	hashdeep -r dir, pipe to a file
	@parameter
	infile: the input file or directory name
	outfile: output file name
	@return
	True if success otherwise False
	"""
	# If outfile is not specified
	if not outfile:
		outfile = infile + HASHDEEP_SUFFIX
	# The input of hashdeep need to be absolute path, otherwise, there will
	# be bug.
	infile = os.path.abspath(infile)
	p = subprocess.Popen(['hashdeep', '-r', infile], stdout=subprocess.PIPE)
	output, error = p.communicate()
	open(outfile, 'w').write(output)
	return False if error else True

def remove(indir):
	""" Remove the decompressed files """
	p = subprocess.Popen(['rm', '-r', indir], stdout=subprocess.PIPE)
	output, error = p.communicate()
	return False if error else True

def find_text_in_dir(indir, text, ignore_binary=True):
	""" Find files containing text in directory """
	flags = '-rlI' if ignore_binary else '-rl'
	p = subprocess.Popen(['grep', flags, text, indir],
			stdout=subprocess.PIPE)
	output, error = p.communicate()
	return filter(bool, output.split("\n"))

def get_hexdigest(infile, func = "sha256"):
	m = getattr(hashlib, func)()
	m.update(open(infile, 'r').read())
	return m.hexdigest()

def digest_batch(infile, outdir=None):
	infile_list = filter(bool, open(infile, 'r').read().split('\n'))
	for infile in infile_list:
		outfile = (outdir + infile.split("/")[-1] + HASHDEEP_SUFFIX if
				outdir else None)
		infile = unpack(infile)
		digest(infile, outfile)
		remove(infile)

"""
Utilities for protocol buffer
"""
def write_proto_to_file(proto, filename):
	f = open(filename, "wb")
	f.write(proto.SerializeToString())
	f.close()

def read_proto_from_file(proto, filename):
	f = open(filename, "rb")
	proto.ParseFromString(f.read())
	f.close()

def read_proto_from_files(proto, field, filenames):
	"""For repeated proto only"""

def write_proto_to_files(proto, field, filenames):
	"""For repeated proto only"""

"""
Utilities for logging 
"""
class GlobalFileEntryDict:
	def __init__(self):
		self.GLOBAL_FILE_ENTRY = "../../data/global_app_entry.dat"
		global_file_entry = evalpb.APKDatabase()
		"""
		If file already exists, just reload it.
		Else ignore and create new one on save.
		"""
		if os.path.exists(self.GLOBAL_FILE_ENTRY):
			read_proto_from_file(global_file_entry, self.GLOBAL_FILE_ENTRY)
		self.global_file_entry_dict = dict()
		for entry in global_file_entry.record:
			self.global_file_entry_dict[entry.digest] = entry
	
	def contains(self, digest):
		return digest in self.global_file_entry_dict

	def get(self, digest):
		return self.global_file_entry_dict[digest]

	def update(self, digest, record):
		self.global_file_entry_dict[digest] = evalpb.APKRecord()
		self.global_file_entry_dict[digest].CopyFrom(record)
	
	def save(self):
		global_file_entry = evalpb.APKDatabase()
		global_file_entry.total = len(self.global_file_entry_dict)
		for digest in self.global_file_entry_dict:
			record = global_file_entry.record.add()
			record.CopyFrom(self.global_file_entry_dict[digest])
		write_proto_to_file(global_file_entry, self.GLOBAL_FILE_ENTRY)

