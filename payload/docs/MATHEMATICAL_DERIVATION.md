# Penurunan Model Matematis dan Logika Simulasi

## 1. Objek dasar: tabung `δ` di `R^3`

Jurnal mendefinisikan `δ`-tube sebagai lingkungan berjarak `δ` dari sebuah ruas garis satuan. Dalam simulasi, ruas garis ditulis

```math
L(t)=c+(t-1/2)v, \qquad 0\le t\le 1,
```

dengan pusat `c ∈ R^3` dan arah satuan `||v||=1`. Sebuah titik `x` termasuk tabung apabila

```math
\min_{0\le t\le 1}\|x-L(t)\|\le \delta.
```

Parameter proyeksi diperoleh dari

```math
t_* = \operatorname{clip}_{[0,1]}
\frac{(x-a)\cdot(b-a)}{\|b-a\|^2},
```

kemudian jarak kuadrat dihitung dari `||x-(a+t_*(b-a))||^2`.

Jurnal memakai skala volume `|T| \sim δ^2`. Program mencatat dua nilai:

```math
|T|_{paper}=\delta^2,
```

serta volume kapsul geometris

```math
|T|_{capsule}=\pi\delta^2+\frac{4}{3}\pi\delta^3.
```

Semua persamaan jurnal dievaluasi dengan `|T|_{paper}` agar skala numeriknya konsisten dengan notasi jurnal.

## 2. Shading dan densitas `λ`

Untuk setiap tabung, simulasi memilih interval acak `[s_0,s_1]⊂[0,1]`. Bagian tabung yang proyeksinya berada di interval ini menjadi `Y(T)`. Densitas diskret dihitung dari

```math
\lambda_{sim}=
\frac{\sum_T |Y(T)|}{\sum_T |T|}.
```

Karena shading berupa interval longitudinal, `|Y(T)|/|T|` didekati oleh `s_1-s_0`.

## 3. Aproksimasi volume gabungan

Kubus `[-1.05,1.05]^3` dibagi menjadi kisi `N^3`. Bila panjang sisi voxel adalah `h`, volume gabungan diperkirakan sebagai

```math
\left|\bigcup_T T\right|_{voxel}
=h^3\#\{q:\mu(q)>0\},
```

sedangkan fungsi multiplicity adalah

```math
\mu(q)=\#\{T:q\in T\}.
```

Identitas massa diskret yang menjadi dasar pemeriksaan multiplicity ialah

```math
\sum_q \mu(q)h^3
\approx \sum_T |T|.
```

## 4. Persamaan utama `(1.1)`–`(1.4)`

Program menghitung sisi kanan berikut:

```math
B_{1.1}=\delta^\varepsilon\lambda^K\sum_T |T|,
```

```math
B_D=\kappa\delta^{\omega+\varepsilon}
(\#\mathbb T)|T|
\big((\#\mathbb T)|T|^{1/2}\big)^{-\sigma},
```

```math
B_E=\kappa\delta^{\omega+\varepsilon}m^{-1}
(\#\mathbb T)|T|
\big(m^{-3/2}\ell(\#\mathbb T)|T|^{1/2}\big)^{-\sigma},
```

serta

```math
B_{1.4}=\delta^\varepsilon\lambda^K m^{-1}(\#\mathbb T)|T|.
```

Nilai tersebut dibandingkan dengan volume union shading hasil voxel. Perbandingan ini hanya diagnostik karena konstanta teoretis berlaku secara asimtotik untuk `δ` cukup kecil.

## 5. Katz–Tao dan Frostman Wolff

Untuk keluarga kotak berorientasi `W`, definisi `(4.1)` memberi estimator

```math
m_{sim}=\max_W
\frac{\#\{T:T\subset W\}|T|}{|W|}.
```

Untuk slab `S`, definisi `(4.2)` memberi

```math
\ell_{sim}=\max_S
\frac{\#\{T:T\subset S\}}{|S|(\#\mathbb T)}.
```

Volume irisan slab dengan bola satuan dihitung tepat melalui integral

```math
|S\cap B(0,1)|=\pi\left[z-\frac{z^3}{3}\right]_{z_{min}}^{z_{max}}.
```

Kotak dan slab disampel secara acak. Karena tidak mungkin menguji semua himpunan konveks, `m_sim` dan `ell_sim` adalah lower estimator terhadap supremum sebenarnya.

## 6. Non-clustering pada prisma

Untuk setiap prisma berukuran `a×b×2`, program mengevaluasi rasio

```math
R_{prism}=
\frac{\#\{T:T\subset W\}}
{100ab\delta^{-2}}.
```

Nilai `R_prism≤1` pada seluruh probe yang disampel konsisten dengan hipotesis Theorem 1.2, tetapi tidak membuktikan hipotesis untuk semua prisma.

## 7. Dekomposisi fine/coarse dan `(1.9)`–`(1.11)`

Tabung dikelompokkan berdasarkan sudut arah pada skala `ρ`. Pada voxel terisi:

```math
\mu_{coarse}(q)=\#\{G:\exists T\in G,\ q\in T\},
```

```math
\mu_{fine}(q)=\frac{\mu(q)}{\mu_{coarse}(q)}.
```

Dengan definisi diskret tersebut, hubungan `(1.10)` berlaku titik demi titik. Program melaporkan median ketiga besaran dan rasio

```math
\frac{\mu}{\mu_{fine}\mu_{coarse}}.
```

Eksponen `ν` diinferensikan dari ukuran grup tipikal:

```math
\#\mathbb T[T_\rho]
=\delta^\nu(\rho/\delta)^2.
```

Setelah mengambil logaritma,

```math
\nu=
\frac{\log(\#\mathbb T[T_\rho]/(\rho/\delta)^2)}{\log\delta}.
```

Batas `(1.9)` dan `(1.11)` kemudian dihitung secara langsung.

## 8. Grains

Skala grain mengikuti penurunan pada bagian vignette:

```math
c\ge \frac{\rho}{\delta}
\big(\#\mathbb T[T_\rho]\big)^{-1/2}.
```

Dimensi grain setelah rescaling adalah

```math
\frac{\delta}{\rho}\times c\times c,
```

sedangkan setelah inverse anisotropic rescaling menjadi

```math
\delta\times \rho c\times c.
```

Program mencatat kedua tripel dimensi ini.

## 9. Broadness `(7.3)`–`(7.4)`

Pada titik voxel yang dilalui sedikitnya dua tabung, program mengukur fraksi arah terbesar yang masuk ke spherical cap berjari-jari sudut `r`:

```math
f(r)=\max_{v_0}
\frac{\#\{v:\angle(v,v_0)\le r\}}{\#V}.
```

Estimator error broadness adalah

```math
K_{broad}(r)=\frac{f(r)}{r^\beta},
\qquad \beta=\omega\zeta/100.
```

## 10. Local density `(1.7)` dan `(1.12)`

Untuk pusat voxel acak dan radius `τ`, program menghitung fraksi voxel bola yang termasuk union shading. Nilai ini dibandingkan dengan

```math
m^{\sigma/2}(\delta/\tau)^{\sigma+\omega}.
```

Konstanta implisit dari simbol `\gtrsim` tidak diketahui, sehingga hasil ditandai sebagai diagnostic ratio.

## 11. Tube doubling `(12.1)`

Radius setiap tube diperbesar dari `δ` menjadi `Rδ`. Program menghitung volume union baru dan membandingkannya dengan

```math
\delta^{-\varepsilon}R^3
\left|\bigcup_T Y(T)\right|.
```

## 12. Mengapa tidak semua persamaan menjadi update law

Jurnal memiliki 254 label persamaan. Banyak di antaranya adalah:

- langkah antara dalam pembuktian;
- ketaksamaan dengan konstanta implisit;
- hasil pigeonholing atau refinement;
- klaim eksistensi objek konveks;
- induksi pada skala;
- relasi yang hanya berlaku setelah memilih subkeluarga tertentu.

Objek seperti itu tidak menentukan algoritma tunggal. Karena itu proyek ini mencatat semua label di `data/equation_registry.csv`, tetapi membedakan formula yang benar-benar dieksekusi dari formula yang hanya dapat dilacak sebagai bagian pembuktian.
