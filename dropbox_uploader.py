#!/usr/bin/env python3
from os import path
from hashlib import sha256
from sys import stdout
import dropbox

token=""
dbx = dropbox.Dropbox(token)

chunk_size=int(0.5*1024**2)
file_path=""

file_name=file_path.split('/')[-1]
file_size=path.getsize(file_path)

print("[*] Logged in as:",dbx.users_get_current_account().name.display_name)
print("[i] Current contents in cloud >>")
bak_file="/"+file_name+".bak"
for i in dbx.files_list_folder('').entries:
	if i.name == bak_file[1:]:
		print("[!] Found a previous bak file. Skipping")
		break
	elif i.name == file_name:
		print("[!] Found same name file, moving to",bak_file)
		dbx.files_move("/"+file_name,bak_file)

for i in dbx.files_list_folder('').entries:
	print("\t",i.name)

file_name="/"+file_name
print("-"*60)

print("[*] Uploading file:",file_path)
print("[*] File size: "+str(file_size/1024**2)+" MB")

f=open(file_path,"rb")

hs=b''
while True:
	chunk=f.read(4*1024**2)
	if len(chunk)==0:
		break
	hs+=sha256(chunk).digest()
chunk=b''
f.seek(0)
con_hash_cal=sha256(hs).hexdigest()
print("[*] Calculated Content Hash: "+ con_hash_cal)
hs=b''

print("[*] Uploading in chunks of size {} MB.".format(chunk_size/1024**2))
up_session_start=dbx.files_upload_session_start(f.read(1))
print("[*] Session id:",up_session_start.session_id)

stdout.write("[+] Upload status:  0.00%")
stdout.flush()
stdout.write("\b"*7+("%6.2f" % (f.tell()*100/file_size)+"%"))
stdout.flush()

cursor=dropbox.files.UploadSessionCursor(up_session_start.session_id,f.tell())
commit=dropbox.files.CommitInfo(file_name)

while f.tell() < file_size:
	if (file_size-f.tell()) <= chunk_size:
		dbx.files_upload_session_finish(f.read(chunk_size),cursor,commit)
		stdout.write("\b"*7+("%6.2f" % (f.tell()*100/file_size)+"%"))
		stdout.flush()
	else:
		dbx.files_upload_session_append(f.read(chunk_size),cursor.session_id,cursor.offset)
		stdout.write("\b"*7+("%6.2f" % (f.tell()*100/file_size)+"%"))
		stdout.flush()
		cursor.offset=f.tell()

f.close()

con_hash=dbx.files_get_metadata(file_name).content_hash
print("\n[+] Uploaded !\n[*] Retrieved Content Hash: "+ con_hash)

if con_hash==con_hash_cal:
	print("[+] Content Hash Matched !\n[i] File Uploaded Successfully !")
	print("[*] Removing bak file...")
	dbx.files_delete(bak_file)
	print("[*] Bak deleted.")
else:
	print("[!] Content Hash Match Failed.")

print("[i] Current contents in cloud >>")
for i in dbx.files_list_folder('').entries:
	print("\t",i.name)
