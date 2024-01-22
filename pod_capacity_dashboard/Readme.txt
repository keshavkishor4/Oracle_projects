Process to Launch the Applications

1. Goto fapod directory and check requirments.txt file
2. pip3 install -r requirments.txt
3. Create .env file and store it into creds directory
3. goto fapod directory run
python3 manage.py migrate
python3 manage.py migrate --run-syncdb
 or
python manage.py migrate
python manage.py migrate --run-syncdb  -- Depends upon the python system which is using
4. Run the application using
goto fapod
python3 manage.py runserver
or
python manage.py runserver

By default application runs on 8000 port
If you want to run application in specific port , please try
python3 manage.py runserver 8001

Once we launch the application , please create superuser for admin console
To create super user
user below command
python manage.py createsuperuser
