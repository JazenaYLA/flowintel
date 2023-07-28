#!/bin/bash
isscripted=`screen -ls | egrep '[0-9]+.fcm' | cut -d. -f1`
source env/bin/activate

function launch {
    screen -dmS "fcm"
    # screen -S "fcm" -X screen -t "recurring_notification" bash -c "python app/notification/recurring_notification.py; read x"
    screen -S "fcm" -X screen -t "recurring_notification" bash -c "python startNotif.py; read x"
    python app.py
}

function killscript {
    if  [ $isscripted ]; then
		screen -X -S fcm quit
    fi
}

function init_db {
	python app.py -i
}

function reload_db {
	python app.py -r
}


if [ "$1" ]; then
    case $1 in
        -l | --launch )             launch;
                                        ;;
		-i | --init_db )            init_db;
                                        ;;
		-r | --reload_db )          reload_db;
                                        ;;
        -ks | --killscript )            killscript;
    esac
    shift
else
	launch
fi
