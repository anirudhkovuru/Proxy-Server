import socket
import os
import time                

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
          
host = ""
portr = 20000
ports = 12345

#server binds to port 12345
s.bind((host, ports))
s.listen(5)

print('Server listening....')

while True:

    #setting up client
    r = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    r.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

    #client connects to main server
    try:
        r.connect((host, portr))
    except Exception as e:
        print('Server error')
        time.sleep(6)

    #server accepting connection from browser
    conn, addr = s.accept()

    #the caching array
    cache = []
    try:
        with open("cache", "r") as cache_var:
            cache = [w.strip() for w in cache_var.readlines()]
    except:
        print("Cache doesn't exist")
    print('\n\ncache = ', end =" ")
    print(cache)
    
    #receiving request from browser
    data = conn.recv(1024)
    data = data.decode('utf-8')

    #filtering all other requests
    if "http://localhost:" not in data:
        continue

    #getting the file name
    temp = data.split( )[1]
    filename = temp.split("/")[3]

    if filename in cache:
        print(filename + " in cache")

        #generate request with If-Modified-Since header
        if_header = 'If-Modified-Since: ' + time.strftime("%a %b %d %H:%M:%S %Y", time.strptime(time.ctime(os.path.getmtime(filename)), "%a %b %d %H:%M:%S %Y")) + '\r\n\r\n'
        if_request = data[:-2] + if_header
        if_request = if_request.replace("http://localhost:" + str(portr), "")

        #sending request to main server
        r.send(bytearray(if_request, 'utf-8'))

        #recieving if response from main server
        if_response = b''
        while True:
            packet = r.recv(1024)
            if not packet:
                break
            if_response += packet
        temporary = if_response[:228].decode('utf-8')
        response_code = temporary.split(" ")[1]

        #Not modified
        if response_code == "304":
            print("Not Modified")
            #open file in cache
            try:
                with open(filename, "rb") as f:
                    cache_response = f.read()
            except Exception as e:
                print("Error opening the file from cache")
                print(e)
                cache.remove(filename)

            #send response to browser
            conn.send(cache_response)

        #Modified
        elif response_code == "200":
            print("Modified")
            #update file in cache
            try:
                with open(filename, "wb") as f:
                    f.write(if_response)
            except Exception as e:
                print("Error opening the file from cache")
                print(e)
                cache.remove(filename)

            #send response to browser
            conn.send(if_response)

    else:
        print(filename + " not in cache")

        #forwarding request to main server
        request = data.replace("http://localhost:" + str(portr), "")
        r.send(bytearray(request, 'utf-8'))

        #recieving response from main server
        response = b''
        while True:
            packet = r.recv(1024)
            if not packet:
                break
            response += packet

        #storing new file into cache
        if filename != '':
            #cache length is maxinmum of 3
            if len(cache) < 3:
                cache.append(filename)
            else:
                cache.append(filename)
                temp_file = cache[0]
                cache.remove(temp_file)

                #remove the old file from the directory
                try:
                    os.remove(temp_file)
                except Exception as e:
                    print(e)
                    print("ERROR: " + temp_file + " does not exist")

            #create new file for new entry in cache
            with open(filename, "wb") as new_file:
                new_file.write(response)

        #send response to browser
        conn.send(response)

    #update cache file with new entries
    with open("cache", "w") as cache_var:
        cache_list = "\n".join(cache)
        cache_var.write(cache_list)

    #close the server connection and client connection
    conn.close()
    r.close()
