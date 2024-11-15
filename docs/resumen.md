# Resumen del back 

## Qué onda los websockets 

Hay una clase `ConnectionManager` que tiene una única instancia `mannager`. A
fines prácticos es una clase estática, aunque esto no existe en Python. 
Puede pensarse que hay un `WebSocket` (canal de comunicación continuo) con 
cada jugador en el servidor, y el manager tiene tres mapeos importantes 
para organizar la comunicación:

- Dado un entero `sid`, puede encontrar el `WebSocket` con identificador `sid`.
- Dado un `game_id`,  da una lista de `sid`s (los `id` de los sockets en esa partida).
- Dado un socket id `sid`, da el `game_id` de la partida donde esta ese socket.

El mapeo que va de `game_id` a una lista `socket_id`s es tal que si se pasa un
`game_id = 0`, los `socket_id` que se devuelven son aquellos cuya conexion se
estableció, pero no se asoció a ninguna partida todavía. Es decir, los sockets
de los jugadores/usuarios que todavía no se unieron a una partida.

Esto es suficiente para poder `broadcast`ear mensajes a todos los jugadores 
en una partida, a todos los jugadores e la sala, enviar mensajes directos 
a un jugador, etc.

## Qué onda detectar figuras?

Definimos una clase que se llama `BooleanBoard`. Una `BooleanBoard` tiene como
atributos $(a)$ un tipo de figura (una string como `h1, h2, s3`), y $(b)$ una matriz
booleana. La matriz booleana es una matriz $6\times 6$ con ceros y unos.

Por cada figura posible en el tablero, definimos una configuración de tablero
que le corresponde, con el nombre de esa figura asociado. Por ejemplo, definimos 

```
    "h10": [[0, 0, 1], 
            [1, 1, 1], 
            [1, 0, 0]]
```

Un algoritmo genera todas las otras formas en que esta misma figura puede
aparecer (en otras posiciones, invertida, etc.). Teniendo todas las variaciones
posibles de cada figura, se toma el tablero de la partida y se lo compara con
las variaciones posibles, detectando las que están presentes. Cada vez que hay
una figura presente, se crea una `BooleanBoard` con el nombre de la figura
correspondiente y la matriz booleana que tiene `1` donde está la figura y `0`
donde no.

Se devuelve una lista de matrices booleanas, cada una correspondiente a una
figura del tablero.

## Qué onda los problemas en la base de datos 

Según lo que yo entendí, más allá de que Julio trató de "asquerosa" la
explicación, es que nuestro problema fue tener las cartas de `Shape` y
`Move` asociadas a un `Player`. Siendo esto así, ¿cómo tener un mismo 
`Player` en dos partidas diferentes, si el mismo tiene un único conjunto 
de cartas asociado? En otras palabras, si un `Player` está en la partida `g1` y
la partida `g2`, ¿cómo llevo el registro de las cartas que tiene en cada
partida, si tales cartas dependen no de la partida sino del `Player`?

A esto se agrega otra complicación. Un objeto `Player`, con su `id` único, se
crea siempre en una partida, no en el lobby. O sea que antes de unirse a una
partida (o crearla), los usuarios no tienen ningún identificador aparte de su
nombre, y no existe un objeto `Player` (con `id`, cartas, y demás) que les
corresponda. 

> Más aún, en el código está definida una correspondencia necesaria 
entre un `Player` y una `Game`, es decir que ya de entrada pusimos como requisito
estático que todo `Game` tiene `Player`s y todo `Player` está en un `Game`.

Nosotros determinamos que el `name` de un `Player` es único, y eso es
importante para que nuestro sistema funcione (porque hacemos llamados como
`Player.get(name = player_name)`, donde si existieran varios jugadores con el
mismo nombre se rompe todo).

Supongo que podríamos haber organizado el sistema de manera tal que hubiera un
objeto más, `User`, que esté atado a diversos `Player`. El `User` se crearía
inmediatamente al entrar al lobby, y los `Player` que corresponden a un `User`
al crear o unirse a una partida. Así creo que hubiéramos podido distinguir qué
cartas tiene cada `Player` en las distintas partidas incluso si corresponden al
mismo `User`. No pensé mucho esta solución pero es para tener algo que decir.

También podríamos haber hecho un parche (horrible) para resolver el problema
sin cambiar la base de datos (porque con poco tiempo era imposible
reestructurar la BD). Podríamos haber creado un `PlayerManager`, una clase
estática que tenga mapeos de tipo `String x Int -> Set(Cards)`. La idea es que
el `PlayerManager`, dado un `player_name` y un `game_id`, pueda decir qué
cartas tenía un jugador dado en una partida dada. Cada vez que un jugador se
une a una partida, se "recupera" con el `PlayerManager` qué cartas tenía el
jugador en esa partida, y se hace que el atributo `Player.shapes` sea sus
cartas de figura (según diga el `PlayerManager`), y lo mismo con
`Player.moves`.

Lo bueno de este parche es que no hay que cambiar la BD: cada `Player` seguiría
teniendo un solo conjunto de cartas todo el tiempo, pero ese conjunto iría
cambiando dependiendo de en qué partida está activo el jugador, usando los
datos que tiene el `PlayerManager`. Lo malo es que cada vez que cambia el
estado de las cartas de un jugador en una partida, habría que avisarle al
`PlayerManager` para que registre el cambio. 

La solución no es tan rara, de hecho ese manejo de las cartas sería re similar
al manejo que hace el `ConnectionManager` de los distintos `WebSockets`. Pero
tampoco pensé mucho si en verdad hubiera funcionado o no, seguro tiene banda 
de complicaciones asociadas. Nos sirve igual como para decir algo que podríamos
haber hecho (cuando nos preguntaron eso nos quedamos todos mudos
aoifiuahefuiefas).

Obvio que no nos habría dado el tiempo de hacer nada de esto, pero bueno al menos 
podemos decir que nos damos cuenta que habían soluciones de compromiso. 

## Cómo se reparten las cartas?

Hay dos funciones involucradas: una que se llama sólo al inicializar la partida, 
y otra que se llama al final de cada turno. 

La que se llama al inicializar la partida es `deal_cards_randomly`. Reparte a
los jugadores sus mazos de figura y sus cartas de movimiento. ¡Ojo! Sólo da *el
mazo* de figuras, no *la mano* de figuras. Obviamente, muestrea *sin
repetición* de entre todas las cartas del juego. 

La que se llama al final de cada turno es `complete_player_hands`. Lo que hace
es, dado un jugador, revisa si su mano de movimientos o su mano de figura están
incompleta. Si lo están, les reparte cartas del mazo de movimientos (que es
global del juego) o del mazo de figuras del jugador hasta completar su mano. 

La función `complete_player_hands` chequea que el jugador no tenga figuras
bloqueadas: si las tiene, no le reparte cartas de figuras, excepto en el caso
en el que le queda sólo la carta de figura bloqueada. En ese caso desbloquea la
figura y completa su mano.

`complete_player_hands` se llama al final de cada turno, pero también se llama
al inicializar la partida, justo después de `deal_cards_randomly`. Su única
función en este caso es completar la mano de figura de los jugadores,
repartiéndoles cartas de sus respectivos mazos de figuras.

## Reclamo de figuras

El reclamo de figuras es bastante directo, pero requiere varios inputs para funcionar.
El endpoint toma:

- En qué partida se quiere hacer el reclamo
- Qué jugador quiere hacer el reclamo 
- Cuál es el ID de la carta de figura que se quiere reclamar 
- Qué movimientos se han jugado en este turno antes de que suceda el reclamo 
- Coordenadas `(x, y)` de la figura que se quiere reclamar en el tablero.

Asumiendo que la información provista es válida (la partida existe, etc.), la
función chequea que de hecho exista la figura enviada en la coordenada `(x,
y)`, usando una función auxiliar que se llama `is_valid_figure`.

Si existe la figura en la posición señalada, el primer efecto de reclamar una
figura es que los movimintos parciales que se habían realizado se vuelven
efectivos. Además, se cambia el color prohibido y se borra la carta de figura
que se reclamó. 

Acá también se chequea $(a)$ si al jugador sólo le queda una carta de figura y
$(b)$ si esa carta está bloqueada. Si ambas cosas son el caso, se desbloquea la
carta de figura. (Esto ya se chequeaba en `complete_player_hands`, aunque capaz
tiene más sentido chequearlo y hacerlo acá, para que el jugador pueda reclamar
la carta ahora desbloqueada en el mismo turno).

También se chequea si el jugador se quedó ya sin cartas de figura, en cuyo caso
se lo declara ganador y se termina la partida.

## Bloqueo de figuras 

Prácticamente idéntico al reclamo de figuras: se chequea que los datos sean
válidos y que de hecho exista la figura señalada en la coordenada `(x, y)`
enviada. La única diferencia es que acá se envía el `id` de la carta de figura
que se quiere bloquear. Si todo está validado, se bloquea la figura y se hacen
efectivos los movimientos parciales,


## Haciendo efectivos los movimientos parciales 

Cada partida tiene dos tableros: el que los jugadores ven, y un tablero tipo
*checkpoint*. El que los jugadores ven se llama `actual_board` (tablero *de
hecho*), y el otro se llama `old_board`. 

Así como en algunos juegos vas avanzando y, cuando morís, retornás a un
checkpoint, el `actual_board` va cambiando y, si el jugador deshace sus
movimientos o termina el turno sin reclamar o bloquear figuras, regresa al
`old_board`. 

Cuando los movimientos parciales de un jugador se hacen efectivos (e.g. reclama
una carta de figura), simplemente se hace `game.old_board = game.actual_board`,
creando el nuevo "checkpoint".




























































