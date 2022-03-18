# JackrabbitRelay Identity

**WORKING DRAFT**

This document details setting up an identity. This should only be used if
you plan to use the Statistatorium or want extremely aggressive
defensiveness. The Statistatorium will NOT work at all without an
identity.

*This is **NOT** a substitute for a reliable and properly configured firewall*.

## Disclaimer

Please note RAPMD Crypto, LLC ("the Company"), does not provide financial
advice. The Company, and any associated companies, owners, employees,
agents or volunteers, do not hold  themselves out as Commodity Trading
Advisors (“CTAs”) or Authorized Financial Advisors  (“AFAs”). The owners,
publishers, employees and agents are not licensed under securities laws 
to address particular investment situations. No information presented
constitutes a  recommendation to buy, sell or hold any security,
financial product or instrument discussed  therein or to engage in any
specific investment strategy.

All content is for informational purposes only. The content provided
herein is not intended to replace or serve as a substitute for any
legal, tax, investment or other professional advice,  consultation or
service. It is important to do your own analysis before making any
investment  based on your own financial circumstances, investment
objectives, risk tolerance and liquidity needs.

All investments are speculative in nature and involve substantial risk of
loss. The Company does not in any way warrant or guarantee the success of
any action you take in reliance on the  statements, recommendations or
materials. The Company, owners, publishers, employees and  agents are not
liable for any losses or damages, monetary or other that may result from
the  application of information contained within any statements,
recommendations or materials.  Individuals must use their own due
diligence in analyzing featured trading indicators, other trading  tools,
webinars and other educational materials to determine if they represent
suitable and  useable features and capabilities for the individual.

Use this Software at your own risk. It is provided AS IS. The Company
accepts no responsibility or liability for losses incurred through using
this software. While The Company has gone to great lengths to test the
software, if you do find any bugs, please report them to us in the
[Jackrabbit Support Server](https://discord.gg/g93TpbV) or on Github, and
we will sort them out. Remember that risk management is your
responsibility. If you lose your account, that's entirely on you.

Past performance is not indicative of future results. Investments involve
substantial risk. Any past  results provided are intended as examples
only and are in no way a reflection of what an individual  could have
made or lost in the same situation.

##  Identity

Running the MakeIdentity program will generate an identity. *This alone does **NOT** activate it*.

Here are several exmples:

```bash
/home/GitHub/JackrabbitRelay $ /home/JackrabbitRelay/Extras/MakeIdentity
{ "Identity":"j0IvR5#_R2*EC-9p>I/,WO73B7Y]LADezS]:bYjSp3db891KdhnA$qw;uZzs!oxVw%Q$B.qfGq~=^%^I,q:[ZNxa9EJ.yu~B>VHzNWT}{ak[BOv:#j)GqaXWcLjV&$v%LH>X5B.53I^h2YV#eyPe9$W-k2w-hnITf+%w^Ni5-kTM%V#=UAO]o3rZ_c,mL+O!7B~Rf>Fg~c&$b)Y>.a]z#[{,;R}O#b,r" }

/home/JackrabbitRelay/Extras/MakeIdentity
{ "Identity":"bB]lzXh2=iT&i2o^TNu$rm97GPtA{)TGa3RS0h<3=%4lZiY-Z/wmsZy[]g0JbiP6nUl3aOKP~jKI9fg&ax/i$;y" }

/home/JackrabbitRelay/Extras/MakeIdentity
{ "Identity":"XLnYo-3:@If%YFS~zOP_e,;qUVERzf/Q2,IhwZx8Ld/MLQtTBXGPw_do^*6qo%#QTd4Vh)}#@T1DVJNL!PoYcP!XK1BcrDB0D.G<" }

/home/JackrabbitRelay/Extras/MakeIdentity
{ "Identity":"JuI3U^oWrd8k9Qm+jQo@ka,poctR^x2)(}jRw#Yc}4>7pB;A(%YV@UurNchoM1c=p6FHlZ.ao_VYud8Z1nB8K6lUuP*AG;0VZi_E>w}rPdw>=wphLGAzdNsl{7A-$%AEk(Q:ZlFH!*NsKND4=9!kyO,Ed^P;P=>HRl%Dz&!vDe4lFzR,BvjoP#*.T>Ly_K2R2VgulCFYct(04f[8_9wLrE1eBhu-=A$GWcG=vZ+b$>&{}pfYH)cFa" }                                                                       

/home/JackrabbitRelay/Extras/MakeIdentity
{ "Identity":"*d]B}ZMm+2<.Br6o&1~Xmqb&e%!<Nf*Ro5(bS(m@FXKU-2Q.m;aO)>34^]t!:*UBeVZJ/om0&nwkeyMRZ*98IJYPw1IWPW6l*Pfa9Jn_mzC.v" }

/home/JackrabbitRelay/Extras/MakeIdentity
{ "Identity":"Sc[iHrYd>bB0=0ajuWBn7Qt{0B/v$mk,Xf:,.TdgS:b@&jGB4~qJ68;9zGUWz!M]F#^g.H2zY[<@qB8.OHW2r<uUE>{(.Ro.MZ]nu1]I,&K${VB9L7R(lho6y8D>h@ubquFKRb1y/(i+~W+ShO#O(F/wpQq}4RuB=" }

/home/JackrabbitRelay/Extras/MakeIdentity
{ "Identity":"79;Jm5jvx68E6#2Yq7SfgvSLqA)QB.rHg3l*]a/Z4[@m]5omr/)4c!&+q30!<5;gZ@:o&#khi,N-QeH]-_Zc/}Of*,/%vT;4gw>Lhjq$AaVWznGk.k.WQ_>nvtqy,#tj7m#)U6<O#~7CmGJi2.=:wsJ0:jNF!GyHKe6HFi%<v(Nr2PU@XdJNrRJj$Cg=+Svmx#SPXMl_&N" }
```

The below command prepares for an **active** identity.

```bash
/home/JackrabbitRelay/Extras/MakeIdentity > /home/JackrabbitRelay/Config/Identity.safe
```

Before we activate it, you need to take the identity in the Identity.safe
file and add it to your orders for TradingView or other REST API
messages. Equilibrium and BlackCrowHunter will automatically pick up the
identity *as long as it is on the same VPS as the identity file*. For
Equilibriums and BlackCrowHunters not on the same server as Relay, copy
the Identity.cfg file into the Config folder on any/all secondary
servers.

Example of the identity added to the order payload.

```json
{ "Exchange":"ftxus","Market":"Spot","Account":"MAIN","Action":"Buy","Asset":"AAVE/USD","Identity":"bB]lzXh2=iT&i2o^TNu$rm97GPtA{)TGa3RS0h<3=%4lZiY-Z/wmsZy[]g0JbiP6nUl3aOKP~jKI9fg&ax/i$;y" }
```

**AFTER** all TradingView payloads have the new identity added to them, 

```bash
cd /home/JackrabbitRelay/Config
mv Identity.safe Identity.cfg
```

As soon as you complete the above steps, any order that does not have the
identity reference will **NOT** be processed and the log will reflect
that. You do not need to reboot or restart anything. At this point, the
Statistatorium will automatically work.

**DO NOT SHARE YOUR IDENTITY WITH ANYONE**. Doing so will give anyone
with it control or your trading.

## Donations

Information regarding donations and supporting Jackrabbit Relay can be found [here](./Documentation/Donations.MD).

