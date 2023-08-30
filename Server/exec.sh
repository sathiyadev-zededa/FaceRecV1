#!/bin/bash
code_path="/home/jeet/FaceRecVer.2/Server"
cmd="cd ${code_path}"
eval $cmd
`touch test`
exec_cmd="python3 main.py --bucketname ${bucketname} --access_key ${acces_key} --secret_password ${access_secret} --port ${port}"
eval $exec_cmd
