# Kredo — una economía donde el valor se crea, no se extrae

*Resumen en español. La matemática completa está en [`../en/mathematics.md`](../en/mathematics.md)
(inglés) y [`../ru/mathematics.md`](../ru/mathematics.md) (ruso); las fórmulas, con etiquetas en
español, en [`../../formulas.md`](../../formulas.md).*

## El problema

Dos modelos habituales cargan una injusticia incorporada. En el **capitalismo de renta**, quien
tiene capital gana más aunque no trabaje: el valor se *extrae* de una posición de propiedad. En la
**comuna**, todos son iguales pero no hay crecimiento ni recompensa a los activos, y aparece el
problema del polizón. Kredo es una **tercera vía**: la recompensa es proporcional a la creación de
valor; los activos ganan más, pero nadie se queda sin nada; y ante un ataque el sistema se defiende solo.

## Dos tokens

El dinero se puede transferir; la confianza no. De esa asimetría nacen dos tokens.

- **V (Contribución)** — dinero de trabajo *y* participación en el club. Paga servicios, da parte del
  beneficio externo y se cambia por dinero real (USDC). Su saldo puede ser negativo: eso es un
  préstamo del sistema. V es **transferible**.
- **R (Reputación)** — *soulbound*. No se transfiere, vende ni regala; solo se gana con el trabajo y
  se quema por infracciones. Sube tu límite de crédito y da peso de voto (por $\sqrt{R}$).

Si la reputación se pudiera comprar, un actor rico capturaría el sistema sin crear valor. Al no ser
transferible, la influencia sigue a la contribución demostrada, no al tamaño de la cartera.

## Cómo nace el dinero

Un recién llegado sin V puede recibir un servicio. El dinero se crea en el trato sin devaluar a nadie:

1. **Trato a crédito.** B pide un servicio a A pero no tiene fondos; el sistema emite V para A y B
   asume una deuda (saldo negativo).
2. **Un regalo para todos.** A la vez se emite un poco de V para todos los miembros activos, para no
   diluir sus ahorros; quien creó más valor recibe más.
3. **El regalo espera en depósito.** Congelado hasta pagar la deuda: pagada → se libera a todos; sin
   pagar en 90 días → se quema. Nadie queda en rojo; sin inflación.
4. **Un freno automático.** El tamaño del regalo ($\varepsilon$) baja cuanto más impagos hay.

## Autodefensa y precio

Tres amenazas, tres respuestas incorporadas: **$\varepsilon$ dinámico** (contra la inflación),
**cola de salida con descuento** (contra el pánico) y **quema por impago** (contra el fraude).

El precio de V es $P=(\text{Fondo}+12\times\text{Ingresos externos})/\text{Total de V}$. Las
operaciones con el fondo son neutrales al precio (demostrado). **Sin ingresos externos, el precio de
V está condenado a caer** — no es un defecto, es una necesidad matemática.

## Por qué confiar en el modelo

La filosofía se formaliza en **cinco axiomas** y **siete invariantes**, se implementa como un
simulador determinista y se somete a estrés. En **315 ejecuciones** —Monte Carlo, barrido de 192
parámetros, pruebas de estrés combinadas y análisis de regímenes— **la economía nunca colapsó**.
Detalles y protocolos: [`../en/validation.md`](../en/validation.md).
