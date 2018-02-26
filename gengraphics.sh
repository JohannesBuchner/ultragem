#!/bin/bash

i=0
echo "extracting fire ..."
for a in 0 1 2 3 4; do
for b in 0 1 2 3 4 5; do

((i++))

convert -crop 64x64+$((34+$b*128))+$((45+$a*128)) explosion_fire.png  fire${i}.png

done
done




for locked in N X 2 3
do

echo "mixing gems with lock $locked ..."
for base in 1 2 3 4 5 6 7
do
# stripes, bombs
for modifier in N stripeH stripeV bomb
do

outfilename="comb${locked}-${base}-${modifier}.png"

if [[ "$locked" == "N" ]]; then
cmd0="convert gem${base}.png"
elif [[ "$locked" == "X" ]]; then
cmd0="convert gem${base}.png gemlock${locked}.png -composite"
else
cmd0="convert gemlock${locked}.png gem${base}.png -composite"
fi

if [[ "$modifier" == "N" ]]; then
cmd1="$cmd0"
else
cmd1="$cmd0 gem${modifier}.png -composite"
fi

$cmd1 $outfilename

done

done

echo "making spark ..."

base="N"
modifier='spark'
outfilename="comb${locked}-${base}-${modifier}.png"

if [[ "$locked" == "N" ]]; then
cmd0="convert gem${modifier}.png"
elif [[ "$locked" == "X" ]]; then
cmd0="convert gem${modifier}.png gem${locked}.png -composite"
else
cmd0="convert gem${locked}.png gem${modifier}.png -composite"
fi
$cmd0 $outfilename

done


