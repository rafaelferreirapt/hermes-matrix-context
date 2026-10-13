# matrix-context — plugin do hermes

Para um bot do hermes no Matrix que só responde quando o mencionam, mas que deve saber o que se disse na sala.

O hermes no Matrix só conhece as mensagens que lhe chegam ao modelo. Num bot que só responde quando o mencionam, isso quer dizer que, quando é chamado a meio de uma conversa, não sabe o que se disse antes.

Este plugin resolve isso sem gastar chamadas ao modelo:

- Nas salas de `MATRIX_CONTEXT_ROOMS`, cada mensagem que não menciona o bot, ou que não vem do dono dele (`MATRIX_ALLOWED_USERS`), fica guardada no disco do próprio hermes e é descartada antes de chegar ao modelo. Não custa nada.
- Quando o dono menciona o bot, a mensagem chega ao modelo com o que se disse nessa thread, ou no nível de topo da sala, desde a última vez que o bot foi chamado lá. O contexto vem marcado como informação, não como instruções.
- As outras salas e as mensagens diretas não são tocadas.

## Instalar

1. Instala o plugin:
   ```
   hermes plugins install <url deste repositório>
   ```
   ou copia esta pasta para `<pasta do hermes>/plugins/matrix-context/`.
2. Ativa-o no `config.yaml`:
   ```yaml
   plugins:
     enabled:
       - matrix-context
   ```
3. No `.env`, a lista das salas partilhadas (IDs separados por vírgulas):
   ```
   MATRIX_CONTEXT_ROOMS=!sala1,!sala2
   ```
   `MATRIX_USER_ID` (o bot) e `MATRIX_ALLOWED_USERS` (o dono) já existem no `.env` do Matrix.
4. No `config.yaml`, as mesmas salas têm de estar em `matrix.free_response_rooms`. Assim o hermes entrega ao plugin todas as mensagens delas, e não só as que mencionam o bot. Quem decide se a mensagem vai ao modelo passa a ser o plugin.
5. Reinicia o hermes. No registo deve aparecer `matrix-context: active in N rooms`. Se faltar alguma variável, aparece `matrix-context: inactive (...)` e o plugin não faz nada.

Opcional:

| Variável                        | Por omissão | Para quê                                                    |
| ------------------------------- | ----------- | ----------------------------------------------------------- |
| `MATRIX_CONTEXT_MAX_MESSAGES`   | 40          | Máximo de mensagens juntadas de cada vez                    |
| `MATRIX_CONTEXT_MAX_CHARS`      | 12000       | Máximo de caracteres juntados de cada vez                   |
| `MATRIX_CONTEXT_RETENTION_DAYS` | 30          | Dias que as mensagens ficam guardadas                       |
| `MATRIX_CONTEXT_BOT_NAMES`      |             | Outros nomes que contam como menção (por exemplo `CFO bot`) |
| `MATRIX_CONTEXT_TZ` | o fuso da máquina | Fuso das horas no contexto (por exemplo `Europe/Lisbon`) |

## O que fica guardado

O texto das mensagens das salas partilhadas, já decifrado, num ficheiro SQLite em `<pasta do hermes>/matrix-context/messages.sqlite3`, durante `MATRIX_CONTEXT_RETENTION_DAYS` dias. É o mesmo que o Element do dono já mostra. Esse ficheiro deve ficar tão protegido como o resto da pasta do hermes.

## Limites

- Só conhece as mensagens que chegaram depois de o plugin estar ativo. O que foi escrito antes não volta.
- Mensagens editadas ficam com o texto original.
- Se o plugin não carregar mas as salas estiverem em `free_response_rooms`, o bot recebe as mensagens do dono sem menção. As instruções da sala devem dizer-lhe para responder `NO_REPLY` quando não é mencionado.
- Feito e testado com o hermes 0.20.4 (hook `pre_gateway_dispatch`).

## Testes

```
cd tests && python -m pytest -q --rootdir . test_context_store.py
```
