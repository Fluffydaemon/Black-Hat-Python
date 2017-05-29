import sys
import socket
import getopt
import threading
import subprocess

# global variables
listen              = False
command             = False
upload              = False
execute             = ""
target              = ""
upload_destination  = ""
port                = 0

def usage():
    print "Netcat script\n"
    print "Usage: netcat_script.py -t target_host -p port"
    print "-l --listen - listen on [host]:[port] for incoming connections"
    print "-e --execute=file_to_run - execute the given file upon receiving a connection"
    print "-c --command - initialize a command shell"
    print "-u --upload=destination - upon receiving connection upload a file and write to [destination]\n"
    
    print "Examples: "
    print "netcat_script.py -t 192.168.0.1 -p 5555 -l -c"
    print "netcat_script.py -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe"
    print "netcat_script.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\""
    print "echo 'ABCDEFGHI' | ./netcat_script.py -t 192.168.11.12 -p 135"
    sys.exit(0)

def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
            usage()
    # read commandline options
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hle:t:p:cu:", ["help","listen","execute","target","port","command","upload"])
    except getopt.GetoptError as err:
        print str(err)
        usage()
    for o,a in opts:
        if o in ("-h","--help"):
            usage()
        elif o in ("-l","--listen"):
            listen = True
        elif o in ("-e","--execute"):
            execute = True
        elif o in ("-c","--comnmandshell"):
            command = True
        elif o in ("-u","--upload"):
            upload_destination = a
        elif o in ("-t","--target"):
            target = a
        elif o in ("-p","--port"):
            port = int(a)
        else:
            assert False,"unhandled option"

def client_sender(buffer):

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # connect to target host
        client.connect((target,port))

        if len(buffer):
            client.send(buffer)

        while True:

            # wait for data back
            recv_len = 1
            response = ""

            while recv_len:

                data        = client.recv(4096)
                recv_len    = len(data)
                response   += data

                if recv_len < 4096:
                    break
            print response,

            # wait for more input
            buffer  = raw_input("")
            buffer += "\n"

    except:

        print "[*] Exception! Exiting."

        # close the connection
        client.close()

def server_loop():
    global target

    # if no target is defined listen on all interfaces
    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target,port))
    print "test"
    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        # start thread to handle client
        client_thread = threading.Thread(target=client_handler, args=(client_socket))
        client_thread.start()

def run_command(command):

    # trim the newline
    command = command.rstrip()

    # run and return output
    try:
        output = subprocess.check_output(command,StandardError=subprocess.STDOUT, shell=True)
    except:
        output = "Failed to execute command.\r\n"

    # return output
    return output

def client_handler(client_socket):
    global upload
    global execute
    global command

    # check upload variable is set
    if len(upload_destination):

        # read in file and write to destination
        file_buffer = ""

        # keep reading data
        while True:
            data = client_socket.recv(1024)

            if not data:
                break
            else:
                file_buffer += data

        # now take bytes and write them out to file
        try:
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()

            # print out file upload successful
            client_socket.send("File successfully uploaded to %s\r\n" % upload_destination)
        except:
            client_socket.send("failed to upload to %s\r\n" % upload_destination)

    # check for command exectution
    if len(execute):

        # run command
        output = run_command(execute)

        client_socket.send(output)

    # another loop if command shell was requested
    if command:
        
        while True:
            # show prompt
            cliet_socket.send("<shell:#> ")

            # wait until (enter key) received
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)

            # send command output back
            response = run_command(cmd_buffer)

            # send back response
            client_socket.send(response)

# is the script listening or sending data via stdin
if not listen and len(target) and port > 0:
    # read in the budder from the commandline
    # this will block, so send CTRL-D if not sending inport
    # to stdin
    buffer = sys.stdin.read()

    # send data off
    client_sender(buffer)

# if listening it will either upload. execute commands or drop a shell back depending on options
if listen:
    server_loop()

main()