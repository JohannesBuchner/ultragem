#!/bin/bash

i=0
for a in 0 1 2 3 4; do
for b in 0 1 2 3 4 5; do

((i++))

convert -crop 64x64+$((34+$b*128))+$((45+$a*128)) explosion_fire.png  fire${i}.png

done
done




for locked in N 2 3
do

for base in 1 2 3 4 5 6 7
do
# stripes, bombs
for modifier in N horizontal vertical square
do

outfilename="comb${locked}-${base}-${modifier}.png"

if [[ "$locked" == "N" ]]; then
cmd0="convert gem${base}.png"
else
cmd0="convert gemlock${locked}.png gem${base}.png -composite"
fi

if [[ "$modifier" == "N" ]]; then
cmd1="$cmd0"
else
cmd1="$cmd0 gem${modifier}.png -composite"
fi

echo $cmd1 $outfilename

done

done

base="spark"
if [[ "$locked" == "N" ]]; then
cmd0="convert gem${base}.png"
else
cmd0="convert gem${locked}.png gem${base}.png -composite"
fi
echo $cmd0 $outfilename

done


