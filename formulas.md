# Formula reference · Справочник формул · Referencia de fórmulas · 公式参考

Equations are language-neutral; each is labelled in English, Russian, Spanish and Chinese.
Full derivations: [`docs/en/mathematics.md`](docs/en/mathematics.md) · [`docs/ru/mathematics.md`](docs/ru/mathematics.md).

---

### Credit limit
$$L(r)=100\,\bigl(1+0.5\ln(1+r)\bigr)$$
- **EN** Maximum a member may go negative, growing with reputation $r$ (log — bounded exposure).
- **RU** Максимальный «минус» участника, растёт с репутацией $r$ (логарифм — ограниченный риск).
- **ES** Máximo saldo negativo de un miembro, crece con la reputación $r$ (log — exposición acotada).
- **ZH** 成员可为负的上限，随声誉 $r$ 增长（对数——风险有界）。

### Auto-score (statistical price sanity)
$$s_a=\exp\!\left(-\tfrac{(|z|-1)^2}{2}\right)\ \text{for}\ |z|>1,\quad z=\tfrac{N-\mu_c}{\sigma_c}$$
- **EN** Trust in a price by its z-score within its category; Gaussian decay past one σ.
- **RU** Доверие к цене по z-оценке внутри категории; гауссово убывание за пределами σ.
- **ES** Confianza en un precio por su z-score dentro de su categoría; caída gaussiana pasada 1σ.
- **ZH** 按类别内 z 分数衡量对价格的信任；超过 1σ 后高斯衰减。

### Confidence
$$\text{confidence}(\tau)=w_a s_a+w_r s_r+w_x s_x,\quad w_a+w_r+w_x=1$$
- **EN** Weighted trust from auto-score, review median and audit.
- **RU** Взвешенное доверие: автооценка, медиана ревью, аудит.
- **ES** Confianza ponderada: auto-score, mediana de revisión y auditoría.
- **ZH** 加权信任：自动评分、评审中位数与审计。

### Dynamic compensation ("gift to all")
$$\varepsilon=\max\!\bigl(0,\ \min(0.95,\ K^\*-1-\kappa\,(\delta-\delta^\*))\bigr)$$
- **EN** Extra V minted per loan; shrinks as the default rate $\delta$ rises (anti-inflation brake).
- **RU** Доп. эмиссия V на кредит; падает с ростом дефолтов $\delta$ (антиинфляционный тормоз).
- **ES** V extra emitida por préstamo; disminuye al subir la tasa de impago $\delta$ (freno antiinflación).
- **ZH** 每笔贷款额外增发的 V；随违约率 $\delta$ 上升而减少（抗通胀刹车）。

### Escrow distribution share
$$\text{Share}(m)=\frac{\text{Turnover}(m)+\xi}{\sum_{m'}\text{Turnover}(m')+n\,\xi}$$
- **EN** A member's share of released escrow, by active turnover (rewards activity, not hoarding).
- **RU** Доля участника в раскрытом escrow — по активному обороту (поощряет активность, не накопление).
- **ES** Parte del escrow liberado según el movimiento activo (premia la actividad, no el acaparamiento).
- **ZH** 成员在释放托管中的份额，按活跃周转（奖励活跃，而非囤积）。

### Welcome grant
$$g_0=\min\!\bigl(100,\ G_t/\mathbb{E}[\text{NewMembers}]\bigr)$$
- **EN** New-member grant from the Genesis Pool; auto-shrinks if growth outpaces earnings.
- **RU** Грант новичку из Genesis Pool; сжимается, если рост обгоняет доход.
- **ES** Subvención al nuevo miembro desde el Genesis Pool; se reduce si el crecimiento supera los ingresos.
- **ZH** 来自 Genesis 池的新成员补助；若增长快于收入则自动缩减。

### Voting power
$$\text{VotingPower}(m)=\sqrt{R(m)}$$
- **EN** Quadratic voting weight; limits whale dominance, and R cannot be bought.
- **RU** Квадратичный вес голоса; ограничивает доминирование китов, R не купить.
- **ES** Peso de voto cuadrático; limita el dominio de las ballenas, y la R no se compra.
- **ZH** 平方投票权重；限制巨鲸主导，且 R 无法购买。

### Price of V
$$P=\frac{F+\mu\cdot\text{ExtRev}}{S},\quad \mu=12$$
- **EN** Price from the fund plus capitalized external revenue over supply.
- **RU** Курс: фонд плюс капитализированная внешняя выручка, делённые на supply.
- **ES** Precio: fondo más ingresos externos capitalizados, sobre la oferta.
- **ZH** 价格：基金加上资本化的外部收入，除以供应量。

### Discounted conversion (bank-run guard)
$$P_{\text{actual}}=P\cdot\min\!\left(1,\ \tfrac{\rho}{\rho^\*}\right),\quad \rho=\tfrac{F}{P\,S},\ \rho^\*=0.3$$
- **EN** When fund coverage $\rho$ drops, conversions are discounted, protecting and restoring the fund.
- **RU** При падении покрытия $\rho$ конвертация идёт со скидкой — защита и восстановление фонда.
- **ES** Cuando la cobertura $\rho$ cae, las conversiones se descuentan, protegiendo y restaurando el fondo.
- **ZH** 当基金覆盖率 $\rho$ 下降时，兑换打折——保护并恢复基金。

### Survival condition
$$\lambda_{\text{rev}}\ \ge\ \tfrac{1}{\mu}\bigl(\text{EmissionRate}\cdot P-\lambda_{\text{inv}}\bigr)$$
- **EN** Minimum external revenue rate to keep the price from permanently falling.
- **RU** Минимальный темп внешней выручки, чтобы курс не падал бесконечно.
- **ES** Tasa mínima de ingresos externos para que el precio no caiga permanentemente.
- **ZH** 维持价格不永久下跌所需的最低外部收入速率。
