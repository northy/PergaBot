#!/usr/bin/env python

#Versão 1.1
versionStr="1.1"

import requests, os, sys, time, datetime, re, argparse, textwrap
from getpass import getpass
from bs4 import BeautifulSoup
from prettytable import PrettyTable

if os.name == 'nt':
	os.system("title PergaBot")
	ostype="w" #windows
else :
	ostype="o" #other

class helpFormatter(argparse.RawDescriptionHelpFormatter) :
	def add_usage(self,usage,actions,groups,prefix=None) :
		if prefix is None :
			prefix = "Uso: "
		return super(helpFormatter, self).add_usage(usage,actions,groups,prefix)

def readArgs() :
	helpEpilog = """Drivers:
	chromedriver (padrão)
	geckodriver
	firefox_binary"""
	#leitura e implementação dos argumentos
	parser = argparse.ArgumentParser(description="PergaBot é um programa feito para a interação automática ou semi-automática com o pergamum por meio de CLI", add_help=False, formatter_class=helpFormatter, epilog=textwrap.dedent(helpEpilog))
	parser._positionals.title = "Argumentos posicionais"
	parser._optionals.title = "Argumentos opcionais"
	parser.add_argument("-h","--help",action="help",default=argparse.SUPPRESS,help="Mostra esta mensagem de ajuda e sai")
	parser.add_argument("-v","--version",help="Imprime a versão do PergaBot e sai",action="version", version="%(prog)s %(versionStr)s")
	parser.add_argument("-a","--auto",help="Modo automático, renova todos os livros marcados como \"Precisa de atenção\" (padrão: falso)", action="store_true")
	parser.add_argument("-d","--driver",help="Seleciona driver para ser usado no selenium, veja Drivers", default="chromedriver", type=str, dest="driverTarget")
	parser.add_argument("-m",help="Argumento para prover a matrícula na inicialização", default='', type=str, dest="mat")
	parser.add_argument("-p",help="Argumento para prover a senha do pergamum na inicialização", default='', type=str, dest="pwd")
	parser.add_argument("-t",help="Tempo em dias para marcar livro como  \"Precisa de atenção\" (padrão: 2)", default=2, type=int, dest="criticalTime")
	parser.add_argument("-s","--status",help="Somente mostra o seu acervo de livros emprestados. (padrão: falso)", action="store_true")
	parser.add_argument("-b","--binary",help="Localização do arquivo do driver (padrão: pasta de execução)", default='', type=str, dest="binaryLoc")
	parser.set_defaults(func=main)
	args=parser.parse_args()
	if (args.driverTarget!="chromedriver" and args.driverTarget!="geckodriver" and args.driverTarget!="firefox_binary") :
		print("Invalid driver: %s"%(args.driverTarget))
		exit(1)
	if (args.binaryLoc == '') :
		args.binaryLoc=os.path.dirname(os.path.abspath(__file__)) + (f"\\{args.driverTarget}.exe" if ostype=='w' else f"/{args.driverTarget}")
	args.func(args)

def main(args) :
	statusMode = args.status
	mat = args.mat
	pwd = args.pwd
	driverTarget = args.driverTarget
	autoMode = args.auto
	criticalTime = args.criticalTime
	binaryLoc = args.binaryLoc

	if not(statusMode) :
		from selenium import webdriver
		from selenium.webdriver.common.keys import Keys
		from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

	url = "http://consulta.uffs.edu.br/pergamum/biblioteca_s/php/login_usu.php" #URL de acesso ao pergamum

	print("Iniciando sessão do requests...")
	with requests.Session() as s:
		
		if not(statusMode) :
			print("Iniciando Selenium Webdriver...")
			if (driverTarget=='chromedriver') :
				options = webdriver.ChromeOptions()
				options.add_argument('headless')
				options.add_argument('--log-level=3')
				driver=webdriver.Chrome(binaryLoc,options=options)
			
			if (driverTarget=='firefox_binary') :
				options = webdriver.FirefoxOptions()
				options.add_argument('-headless')
				binary = FirefoxBinary(binaryLoc)
				driver = webdriver.Firefox(firefox_binary=binary,options=options)
			
			if (driverTarget=="geckodriver") :
				options = webdriver.FirefoxOptions()
				options.add_argument('-headless')
				driver = webdriver.Firefox(executable_path=r"".join(binaryLoc),options=options)
				
			driver.get(url)
			request_cookies_selenium = driver.get_cookies()
			
			for c in request_cookies_selenium : s.cookies.set(c['name'], c['value'])
		
		#Dados para o request
		if (mat=='' or pwd=='') : print("\nInsira os dados para login no pergamum...")
		if (mat=='') : mat=input("Matricula: ")
		if (pwd=='') : pwd=getpass("Senha: ")
		headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36',
			'Referer': url,
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
		if (logged_url.find('meu_pergamum')==-1): print("Erro de login"); exit(0) ##
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
		if (books_names==[]) : print("NENHUM"); exit(0) ##
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
			if ((datetime.datetime.now() + datetime.timedelta(days=criticalTime)) >= (datetime.datetime.strptime(books_exp[i],'%d/%m/%Y'))) : needs_renew[i]=True

		#Print dos dados
		t = PrettyTable(['Nome', 'Data de expiraçação'])
		for i in range(len(books_names)) :
			t.add_row([books_names[i], books_exp[i]+(' *' if needs_renew[i] else '')])
		print(t)
		print("\"*\" = Precisa de atenção para ser renovado")
		
		if (statusMode) : exit()
		
		print()
		
		#Confirmação de quais renovar
		if not(autoMode) :
			print("Quais livros deseja renovar? (0=nenhum) ",end='')
			books_to_renew=list(input().split(','))
			print()
			if len(books_to_renew)==0 or books_to_renew.count('0')>0 : print("Nada para renovar, saindo..."); exit(0) ##
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
			if len(books_to_renew)==0 : print("Nada para renovar, saindo..."); exit(0) ##
		
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
			renovarBtns = driver.find_elements_by_class_name("btn_renovar")
			renovarBtns[i].send_keys(Keys.RETURN)
			time.sleep(3)
			#if (driver.current_url.find('erro')!=-1) : print("ERRO...")
			#else : print("Sucesso...")	
			driver.execute_script("window.history.go(-1)")
			time.sleep(3)
		
		print("\nFim...")
		driver.quit()
		
if __name__=="__main__" :
	readArgs()
