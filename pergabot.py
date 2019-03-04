#! /usr/bin/env python

#Versão 1.0
version="1.0"

import requests, os, sys, time, datetime, re
from getpass import getpass
from bs4 import BeautifulSoup
from prettytable import PrettyTable

if os.name == 'nt':
	os.system("title PergaBot")
	ostype="w" #windows
else :
	ostype="o" #other

ajuda="""uso: ./pergabot.py [opções] ... [-d driver | -m matrícula | -p senha] ...
Opções e argumentos:
-a  | --auto                 : modo automático, renova todos os livros marcados como "Precisa de atenção" (padrão: falso)
-d  | --driver  <driver>     : seleciona driver para ser usado no selenium, veja Drivers
-m              <matrícula>  : argumento para prover a matrícula na inicialização
-p              <senha>      : argumento para prover a senha do pergamum na inicialização
-t              <tempo>      : tempo em dias para marcar livro como  "Precisa de atenção" (padrão: 2)
-s  | --status               : somente mostra o seu acervo de livros emprestados. (padrão: falso)
-b | --binary  <location>    : localização do arquivo do driver (padrão: pasta de execução)
--version                    : printa a versão do PergaBot

Drivers:
chromedriver (padrão)
*geckodriver (TODO)"""

#leitura e implementação dos argumentos
automode = False
drivertarget='chromedriver'
mat=''
pwd=''
criticaltime=2
statusmode=False
binary_loc=os.path.dirname(os.path.abspath(__file__)) + ('\chromedriver.exe' if ostype=='w' else '/chromedriver')
i=1
while (i<len(sys.argv)) :
	if (sys.argv[i]=='-?' or sys.argv[i]=='/?' or sys.argv=='--help') :
		print(ajuda)
		exit() ##
	if (sys.argv[i]=='--version') :
		print("Pergabot versão",version,end='\n\n')
	elif (sys.argv[i]=="-a" or sys.argv[i]=="--auto") :
		automode = True
	elif (sys.argv[i]=="-s" or sys.argv[i]=="--status") :
		statusmode = True
	elif (sys.argv[i]=="-b" or sys.argv[i]=="--binary") :
		i+=1
		binary_loc = sys.argv[i]
	elif (sys.argv[i]=="-d" or sys.argv[i]=="--driver") :
		i+=1
		if (sys.argv[i]=="chromedriver") : drivertarget="chromedriver"
		elif (sys.argv[i]=="geckodriver") : drivertarget="geckodriver"
		else :
			print("Driver não suportado: \"%s\"\n"%sys.argv[i])
			print("Veja ./pergabot.py --help")
			exit() ##
	elif (sys.argv[i]=="-m") :
		i+=1
		mat=sys.argv[i]
	elif (sys.argv[i]=="-p") :
		i+=1
		pwd=sys.argv[i]
	elif (sys.argv[i]=="-t") :
		i+=1
		try:
			criticaltime=int(sys.argv[i])
		except:
			print("Ocorreu um erro na conversão do tempo: \"%s\"\n"%sys.argv[i])
			print("Veja ./pergabot.py --help")
			exit() ##
	else :
		print("Argumento inválido: \"%s\"\n"%sys.argv[i])
		print("Veja ./pergabot.py --help")
		exit() ##
	i+=1

if not(statusmode) :
	from selenium import webdriver
	from selenium.webdriver.common.keys import Keys
	from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

url = "http://consulta.uffs.edu.br/pergamum/biblioteca_s/php/login_usu.php" #URL de acesso ao pergamum

print("Iniciando sessão do requests...")
with requests.Session() as s:
	
	if not(statusmode) :
		if (drivertarget=='chromedriver') :
			options = webdriver.ChromeOptions()
			options.add_argument('headless')
			options.add_argument('--log-level=3')
			#driver=webdriver.Chrome(executable_path=driverpath)
			print("Iniciando Selenium Webdriver...")
			driver=webdriver.Chrome(binary_loc,options=options)
		
		if (drivertarget=='firefox_binary') :
			binary = FirefoxBinary(binary_loc)
			driver = webdriver.Firefox(firefox_binary=binary)
			
		driver.get(url)
		request_cookies_selenium = driver.get_cookies()
		
		for c in request_cookies_selenium : s.cookies.set(c['name'], c['value'])
	
	#Dados para o request
	if (mat=='' or pwd=='') : print("\nInsira os dados para login no pergamum...")
	if (mat=='') : mat=input("Matricula: ")
	if (pwd=='') : pwd=getpass("Senha: ")
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36',
		'Referer': 'http://consulta.uffs.edu.br/pergamum/biblioteca_s/php/login_usu.php?flag=index.php',
		'Host': 'consulta.uffs.edu.br',
		'Connection': 'keep-alive'
	}
	auth_data = {
		'flag': 'index.php',
		'login': mat,
		'password': pwd,
		'button': 'Access',
		'numero_mestre': '',
		'ifsp_categ': '',
		'lab_com_solicitacao': ''
	}
	print()
	
	#Request
	s.get(url, headers=headers)
	web_r = s.post(url, data=auth_data, headers=headers)
	logged_url=web_r.url
	
	#Teste de conexão
	if (logged_url.find('meu_pergamum')==-1): print("Erro de login"); exit() ##
	print("Login realizado com sucesso!\nUsuário: ",end='')
	web_soup=BeautifulSoup(web_r.content, 'lxml')
	u= str(web_soup.find(attrs={"id": "nome"}))
	print(u[re.compile(r'<strong>').search(u).span()[1]:re.compile(r'</strong>').search(u).span()[0]])
	print()
	
	#Extração dos dados dos livros
	books_div = str(web_soup.find(attrs={"class": "c1"}))
	#print(books_div)
	
	#Extração dos nomes dos livros
	print("Livros pendentes:")
	books_names = re.findall(r'title=".*"',books_div)
	if (books_names==[]) : print("NENHUM"); exit() ##
	else :
		for i in range(len(books_names)) :
			books_names[i]=books_names[i].replace('&lt;b&gt;','')
			books_names[i]=books_names[i].replace('&lt;/b&gt;','')
			books_names[i]=re.sub(r'(\s"|title=")','', books_names[i])
			books_names[i]=re.sub(r'\s\s\s',' ', books_names[i])
			books_names[i]=re.sub(r'\s\s',' ', books_names[i])
	
	#Extração dos dias de expiração
	needs_renew=[False]*len(books_names)
	books_exp = re.findall(r'\d\d/\d\d/\d\d\d\d',books_div)
	for i in range(len(books_exp)) :
		if ((datetime.datetime.now() + datetime.timedelta(days=criticaltime)) >= (datetime.datetime.strptime(books_exp[i],'%d/%m/%Y'))) : needs_renew[i]=True

	#Print dos dados
	t = PrettyTable(['Nome', 'Data de expiraçação'])
	for i in range(len(books_names)) :
		t.add_row([books_names[i], books_exp[i]+(' *' if needs_renew[i] else '')])
	print(t)
	print("\"*\" = Precisa de atenção para ser renovado")
	
	if (statusmode) : exit()
	
	print()
	
	#Confirmação de quais renovar
	if not(automode) :
		print("Quais livros deseja renovar? (0=nenhum) ",end='')
		books_to_renew=list(input().split(','))
		print()
		if len(books_to_renew)==0 or books_to_renew.count('0')>0 : print("Nada para renovar, saindo..."); exit() ##
		for b in books_to_renew.copy() :
			if b.find('-')!=-1 :
				for i in range(int(b[0])-1,int(b[2])) :
					books_to_renew.append(i)
			else :
				books_to_renew.append(int(b)-1)
			del books_to_renew[books_to_renew.index(b)]
		books_to_renew=list(set(books_to_renew)); books_to_renew.sort()
	else :
		books_to_renew=[i for i in range(len(needs_renew)) if needs_renew[i]]
		if len(books_to_renew)==0 : print("Nada para renovar, saindo..."); exit() ##
	
	print("Iniciando processo de renovação...")
	print("Injetando cookies no selenium...\n")
	
	#Chamada do selenium
	dict_webr_cookies = web_r.cookies.get_dict()
	response_cookies_selenium = [{'name':name, 'value':value} for name, value in dict_webr_cookies.items()]
	for c in response_cookies_selenium : driver.add_cookie(c)
	driver.get(logged_url)
	
	print("Começando a renovar livro a livro...\n")
	
	#Chamada de renovar
	for i in books_to_renew :
		print("Renovando livro: %s... "%books_names[i])
		renovarBtns = driver.find_elements_by_class_name("btn_renovar");
		renovarBtns[i].send_keys(Keys.RETURN)
		time.sleep(3)
		if (driver.current_url.find('erro')!=-1) : print("ERRO...")
		else : print("Sucesso...")	
		driver.execute_script("window.history.go(-1)")
		time.sleep(3)
	
	print("\nFim...")
	