cat .env | while read line ; do heroku config:set $line ; done
