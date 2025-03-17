# Limits of Rational functions as $x\rightarrow c$

>  Reminder: Rational functions are of the form $f(x)=\frac{p(x)}{q(x)}$, where $p(x)$ and $q(x)$ are polynomials. 
>  e.g. $f(x)=\frac{x^2+3x-5}{x^2-2x+4}$
>  
	We want to compute $\lim_{x \to c} f(x)$

- Case A:
	- If $q(c) \neq 0$, then $\lim_{x \to c} f(x) = f(c) = \frac{p(c)}{q(c)}$
	- e.g $\lim_{x \to 5} \frac{x^2+3x-5}{x^2-2x+4} = \frac{35}{19}$}
- Case B:
	- If $q(c) = 0 \& p(c) \neq 0$, then $\lim_{x \to c} f(x) \text{ does not exist}$
	- e.g. $\lim_{x \to 5}\frac{3x + 1}{x^2-8x+15} \text{ does not exist, because } = \frac{16}{0}$
Find the roots of $f(x)$ and factorize.
	$x_1,_2=\frac{5\pm\sqrt{25-24}}{2}=\frac{5\pm1}{2}=\frac{5\pm1}{2}\implies x_1=3, x_2=2$
- Case C:
	- If $p(c) = 0 \& q(c) = 0, \text{then } x=c\text{ is a root for both } p(x) \& q(x)$
		$\implies (x-c)) \text{ is a common factor for both } p(x) \& q(x)$ 
		This means that $(x-c)$ can be cancelled (simplified). For the new version of $f(x)$ we try again to compute the limit. 
		- e.g. $\lim_{x \to 5}\frac{x^2-3x-10}{x^2-8x+15} = (\frac{0}{0})$
			- This means that $x=5$ is a common root and $(x-5)$ is a common factor for both $p(x) \& q(x)$
			- $\implies \lim_{x \to 5}\frac{(x-5)(x+2)}{(x-5)(x-3)}=$
			 $=\lim_{x \to 5}\frac{x+2}{x-3} = \frac{7}{2}$
		- e.g. $\lim_{x \to 6}\frac{x-6}{x^2-12x+36}=(\frac{0}{0})$
		- $\implies \lim_{x \to 6}\frac{(x-6)}{(x-6))x-6)}$
		- $=\lim_{x \to 6}\frac{1}{x-6}=\frac{1}{0}$
		- $x^2+bx+c=(x+d)(x+e) \text{ where } d*e=c\space \& \space d+e=b$
