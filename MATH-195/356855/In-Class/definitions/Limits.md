# Limits

- e.g. $f(x) = x^2 -x +1$
  - We are interested in the behavior of $f(x)$ as $x$ gets close to $2$.
    - __NOTE:__ we are not interested in the value of $f(2)$.

  And we write this behavior as
      $\lim_{x \to 2} f(x) =3$
- As $x \rightarrow 2$, $f(x)$ gets close to $3$.
  - where "$\rightarrow$" is a symbol for "approaches" or "gets close to".
  - 
## One-Sided Limits

  - e.g. find $\lim_{x \to 0} \frac{|x|}{x}$
      - Reminder: $|x|$ = $\begin{cases} x & \text{if } x \geq 0 \\ -x & \text{if } x < 0 \end{cases}$
    - $\frac{|x|}{x}$ = $\begin{cases} 1 & \text{if } x > 0 \\ -1 & \text{if } x < 0 \end{cases}$
  #### Why is there a little "$^+$" in "$\lim_{x \to 0^+} \frac{|x|}{x}$"?
  - Because we are only interested in the behavior of $\frac{|x|}{x}$ as $x$ gets close to $0$ from the right.
      - So, we have to investigate separately the one-sided limits:
    - "$\lim_{x \to 0^+} \frac{|x|}{x}$" is the behavior of $\frac{|x|}{x}$ as $x$ gets close to $0$ from the right.
      - Therefore, $\lim_{x \to 0^+} \frac{|x|}{x} = 1$

  ##### Similarly, _"$\lim_{x \to 0^-} \frac{|x|}{x}$"_ is the behavior of $\frac{|x|}{x}$ as $x$ gets close to $0$ from the left.

  - Therefore, $\lim_{x \to 0^-} \frac{|x|}{x} = -1$

    ___Important result:___
      $\lim_{x \to 0} \frac{|x|}{x}$ exists ___if and only if___ $x\rightarrow k$
      - $\lim_{x \to k^+} \frac{|x|}{x} = \lim_{x \to k^-} \frac{|x|}{x}$

## Infinite Limits

- These are limits which are equal to $+\infty$ or $-\infty$.
  - e.g. $\lim_{x \to 0} \frac{1}{x^2} = \infty$
    - As $x$ gets close to $0$, $\frac{1}{x^2}$ gets larger.
  - e.g. $\lim_{x \to 0} \frac{1}{x} = -\infty$
    - As $x$ gets close to $0$, $\frac{1}{x}$ gets smaller.
  - _Example:_ $f(x) = \frac{1}{(x-5)^2}$. Find $\lim_{x \to 5} f(x)$.
    - As $x$ gets close to $5$, $f(x)$ gets larger.
    - $$\begin{cases} x \space\space 4.9 \space 4.99 \space 4.999\\ f(x) \space\space 10^2 \space 10^4 \space 10^6 \end{cases}$$
  - This is basically the only time that you will see something approaching infinity in mathematics.
  - __NOTE:__ $\infty$ is not a number, it is a concept.
## Limits at Infinity:

  - These are limits where $x\rightarrow \infty$ or $x\rightarrow -\infty$.
    - e.g. $\lim_{x \to +\infty} \frac{1}{x-6} = 0$
      - As $x$ gets larger and larger, $\frac{1}{x}$ gets smaller and smaller.
      - $x\rightarrow -\infty$

## Computing Limits
  Let "$\lim_{}$" represent any limit, and "$c$" be any constant.
1. $\text{lim }[f(x)\pm g(x)] = \text{lim } f(x) \pm \text{lim } g(x)$
2. $\text{lim }[f(x)\cdot g(x)] = \text{lim } f(x) \cdot \text{lim } g(x)$
3. $\text{lim }[\frac{f(x)}{g(x)}] = \frac{\text{lim } f(x)}{\text{lim } g(x)}$
4. $\text{lim }c \cdot f(x) = c \cdot \text{lim } f(x)$
5. $\text{lim }[f(x)]^k = [\text{lim } f(x)]^k$
6. $\text{lim }c = c$
7. $\lim_{x \to c} f(x) = f(c)$
8. $\lim_{x \to 0^+} \frac{1}{x} = +\infty$, $\lim_{x \to 0^-} \frac{1}{x} = -\infty$

e.g. :
- $lim_{x \to -2} (\frac{2x+3}{11x+6})^3 = (\frac{\lim_{x \to -2} 2x+3}{\lim_{x \to -2} 11x+6})^3$
- $=$ $(\frac{2(-2)+3}{11(-2)+6})^3$
- $= (\frac{-1}{-16})^3 = (\frac{1}{16})^3 = \frac{1}{4096}$

## Limits of Polynomials

___Reminder:__ Polynomials are:_

- _$a_nx^n + a_{n-1}x^{n-1} + \cdots + a_1x + a_0$_

- Where $a,b,\cdots, c$ are real numbers and $n$ is a non-negative integer.
- e.g. $f(x) = 7x^6 - 3x^2 +1$

If  $f(x)$ is a __polynomial__, _then_:
- $\lim_{x \to k} f(x) = f(k)$
  - e.g. $\lim_{x \to 3} (5x^2 - 2x + 4) = 5 \cdot 3^2 - 2 \cdot 3 + 4 = 43$