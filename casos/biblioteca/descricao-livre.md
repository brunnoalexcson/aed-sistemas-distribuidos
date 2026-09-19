<!--
GRUPO DE CONTROLE do experimento.

Este arquivo descreve EXATAMENTE o mesmo sistema de casos/biblioteca/requisitos-biblioteca.md,
porém em texto livre e informal — o modo como um cliente descreveria o sistema
a um desenvolvedor, sem processo de engenharia de requisitos.

É medido pela MESMA suíte de testes do braço de tratamento. A diferença de
conformidade entre os dois braços é o efeito atribuível ao artefato.

Redigido a partir da mesma lista de funcionalidades, sem consultar o documento
estruturado durante a escrita, para não herdar sua precisão.
-->

# Sistema de biblioteca

Preciso de uma API REST em Python para gerenciar a biblioteca aqui do bairro.

A ideia é a seguinte: a gente tem um acervo de livros e um cadastro de usuários,
e precisa controlar os empréstimos. O bibliotecário cadastra os livros (título,
autor e ISBN) e os usuários (nome e e-mail). Depois ele consegue listar os livros,
buscar um livro específico e também excluir um livro do acervo quando ele sai de
circulação — mas claro, não dá pra excluir um livro que está emprestado no momento.

Quando alguém pega um livro emprestado, o sistema registra o empréstimo e o livro
fica indisponível pros outros. O prazo de devolução é de duas semanas. Tem algumas
regras: cada usuário pode ter no máximo 3 livros emprestados ao mesmo tempo,
usuário inativo não pode pegar livro, e quem está devendo multa também fica
impedido até quitar.

Na devolução o livro volta a ficar disponível e, se a pessoa atrasou, o sistema
calcula uma multa de um real e cinquenta por dia de atraso, que fica pendente na
conta do usuário. Depois o bibliotecário pode registrar o pagamento dessa multa
para zerar a pendência.

Também quero conseguir ver a lista de empréstimos de um usuário, e poder filtrar
só os que ainda estão em aberto.

Não precisa de login nem de tela, é só a API mesmo. Pode guardar tudo em memória,
não precisa banco de dados. E o sistema tem que tratar os erros direito, retornando
os códigos HTTP certos quando alguma coisa não existe ou quando alguma regra é
violada.
