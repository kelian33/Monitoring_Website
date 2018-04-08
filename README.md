# Monitoring de site web

Installer le projet
-
Commencez par cloner le projet :

	git clone https://github.com/kelian33/Monitoring_Website.git

Il faut maintenant ajouter les modules complémentaire qu'aura besoin le programme. Utilisez la commande **pip3 install** pour installer les différents paquets :

	pip3 install passlib
	pip3 install flask
	pip3 install mysql-connector
	pip3 install requests
	pip3 install apscheduler

Une fois toutes les librairies installées, il faut créer un fichier nommé *secret_config.py*
Dans ce fichier vous y mettez vos identifiants d'accès à la base, ainsi que la base à utiliser...
Vous trouverez un fichier SQL *monitoring_website.sql* dans lequel se trouve un exemple de base. (Je vous conseille de partir de cette base)

    #Database config
    DATABASE_HOST = 'host'
    DATABASE_USER = 'username'
    DATABASE_PASSWORD = 'password'
    DATABASE_NAME = 'database'
    SECRET_KEY = 'whatyouwant' 

Exécuter le programme
-
Vous pouvez dès à présent lancer l'application avec la commande 

	chmod +x app.py   //Rend le fichier executable
	./app.py //Lance le programme