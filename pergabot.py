import requests
import re
import datetime, time
from bs4 import BeautifulSoup

versionStr="1.2"

class Pergabot() :
    def __init__(self, **kwargs) :
        """
        Instancia a classe Pergabot.
        
        Attributes:
            verbose (bool): Indica se o programa imprimirá o que está fazendo no momento
            login (str): Login do pergamum do usuário
            password (str): Senha do pergamum do usuário
            headers (dict): Cabeçalhos enviados nos requests
            auth_post_data (dict): Dados para o request post da autenticação
            login_url (str): URL da página de login do pergamum
            dashboard_url (str): URL da página principal do pergamum (quando o usuário está logado)
            critical_time (int): Número em dias para a renovação automátic
            session (requests.Session): Sessão do requests usada para armazenar os cookies
            soup_cache (bs4.beautifulSoup): Cache para o objeto não ser recalculado quando necessário.
        """

        self.verbose = False
        self.login_name = None
        self.password = None
        self.headers = None
        self.auth_post_data = None
        self.login_url = None
        self.dashboard_url = None
        self.critical_time = 2
        self.session = requests.Session()
        self.soup_cache = None

        self.__dict__.update(kwargs)
    
    class Book() :
        def __init__(self,name,expiration_day,needs_renew) :
            """
            Instancia a classe Pergabot.Book.

            Attributes:
                name (str): Nome do livro
                expiration_day (str): Data do dia de expiração do livro
                needs_renew (bool): Indica se o livro está no prazo de renovação automática
            """
            self.name = name
            self.expiration_day = expiration_day
            self.needs_renew = needs_renew
    
    class PergabotException(Exception) :
        pass

    def set_attributes(self, **kwargs) :
        """
        Modifica os atributos da classe para os passados.

        Args:
            kwargs (dict): Dicionário dos atributos a serem utilizados
        """
        self.__dict__.update(kwargs)
    
    def login(self) :
        '''Efetua login no pergamum.'''
        self.soup_cache = None
        if self.login_url == None :
            raise self.PergabotException("URL de login inexistente.")

        response = self.session.post(self.login_url, data=self.auth_post_data)
        if not(self.is_logged()) :
            raise self.PergabotException("Falha de login.")
        if self.verbose : 
            print(f"Login realizado com sucesso!\nUsuário: {self.get_user_name()}")
            print()
        
    def is_logged(self) :
        """
        Checa se a sessão está logada no pergamum.

        Returns:
            bool: True se está logado ou False se não
        """
        response = self.session.get(self.dashboard_url)
        return True if (self.dashboard_url in response.url) else False

    def get_soup(self) :
        """
        Getter.

        Returns:
            bs4.BeautifulSoup: Objeto BeautifulSoup com os elementos do pergamum.
        """
        if self.soup_cache != None : return self.soup_cache
        if self.is_logged() :
            response = self.session.get(self.dashboard_url)
            self.soup_cache = BeautifulSoup(response.content, 'lxml')
            return self.soup_cache
        else :
            raise self.PergabotException("Usuário não autenticado.")

    def get_user_name(self) :
        """
        Getter.

        Returns:
            str: String contendo o nome do usuário.
        """
        if self.is_logged() :
            soup=self.get_soup()
            u=str(soup.find(attrs={"id": "nome"}))
            return u[re.compile(r'<strong>').search(u).span()[1]:re.compile(r'</strong>').search(u).span()[0]]
        else :
            raise self.PergabotException("Usuário não autenticado.")

    def set_login_password(self,login_name,password) :
        """
        Modifica os atributos de login e senha.

        Args:
            login (str): Login do usuário
            password (str): Senha do usuário
        """
        self.login_name = login_name
        self.password = password
        self.__update_auth_post_data()

    def get_books(self) :
        """
        Retorna os livros do usuário.

        Returns:
            list: Vetor de objetos Pergabot.Book contendo os livros do usuário (None se não tiver nenhum)
        """
        if not(self.is_logged()) :
            raise self.PergabotException("Usuário não autenticado.")
        soup = self.get_soup()
        books_div = str(soup.find(attrs={"class": "c1"}))

        books = []

        #Names
        books_names = re.findall(r'title=".*"',books_div)
        if (books_names==[]) : return None
        else :
            for i in range(len(books_names)) :
                books_names[i]=books_names[i].replace('&lt;b&gt;','').replace('&lt;/b&gt;','')
                books_names[i]=re.sub(r'(\s"|title=")','', books_names[i])
                books_names[i]=re.sub(r'\s\s\s',' ', books_names[i])
                books_names[i]=re.sub(r'\s\s',' ', books_names[i])
        
        #Expirations
        needs_renew=[False]*len(books_names)
        books_exp = re.findall(r'\d\d/\d\d/\d\d\d\d',books_div)
        for i in range(len(books_exp)) :
            if ((datetime.datetime.now() + datetime.timedelta(days=self.critical_time)) >= (datetime.datetime.strptime(books_exp[i],'%d/%m/%Y'))) : needs_renew[i]=True
        
        for i in range(len(books_names)) :
            books.append(self.Book(books_names[i],books_exp[i],needs_renew[i]))
        
        return books

    def renew(self, books_to_renew) :
        """
        Renova os livros do usuário.

        Args:
            books_to_renew (list): Vetor de inteiros indicando quais livros renovar por índice.
        """
        if not(self.is_logged()) :
            raise self.PergabotException("Usuário não autenticado.")
        if self.verbose :
            print("Iniciando processo de renovação...")
            books = self.get_books()

        soup = self.get_soup()

        html_reduced_id = str(soup.findAll(attrs={"id":"id_codigoreduzido_anteriorPendente"}))
        reduced_id = html_reduced_id[re.compile(r'value="').search(html_reduced_id).span()[1]:re.compile(r'"/').search(html_reduced_id).span()[0]]
        renew_btns_data = soup.findAll(attrs={"class": "btn_renovar"})
        renew_attrs = []
        for btn in renew_btns_data :
            btn=str(btn)
            renew_attrs.append(list(btn[re.compile(r'\(').search(btn).span()[1]:re.compile(r'\)').search(btn).span()[0]].replace("'",'').split(',')))
        if self.verbose : print("Começando a renovar livro a livro...\n")
        
        #Chamada de renovar
        for i in books_to_renew :
            if self.verbose : print("Renovando livro: %s... "%books[i].name)
            renew_url=self.dashboard_url+"?rs=ajax_renova&rst=&rsrnd={}&rsargs[]={}&rsargs[]={}&rsargs[]={}&rsargs[]={}".format(int(time.time() * 1000),renew_attrs[i][0],renew_attrs[i][1],renew_attrs[i][2],reduced_id)
            response=self.session.get(renew_url)
            if self.verbose : print(response)

    def __update_headers(self) :
        '''Atualiza o cabeçalho que será utilizado nas requisições.'''
        self.session.headers.update({
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36',
			'Referer': self.login_url,
			'Connection': 'keep-alive'
		})
    
    def __update_auth_post_data(self) :
        '''Atualiza os dados que serão enviados no request post da autenticação'''
        self.auth_post_data = {
			'flag': 'index.php',
			'login': self.login_name,
			'password': self.password,
			'button': 'Access',
			'numero_mestre': '',
			'ifsp_categ': '',
			'lab_com_solicitacao': ''
		}
    
    def set_login_url(self,url) :
        """
        Modifica o atributo da url de login.

        Args:
            url (self): URL a ser utilizada.
        """
        self.login_url = url
        self.__update_headers()
    
    def set_dashboard_url(self,url) :
        """
        Modifica o atributo da url da página principal.

        Args:
            url (self): URL a ser utilizada.
        """
        self.dashboard_url = url