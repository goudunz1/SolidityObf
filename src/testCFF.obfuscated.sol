pragmasolidity 0.8.28;
contract PrimeChecker{
  function isPrime(uint256 number)external pure returns(bool){
    uint256 state0=0;
    if(state0==0){
      if(number<=1){
        state0=1;
      }else{
        state0=2;
      }
    }
    if(state0==1){
      return false;
      state0=0;
    }
    if(state0==2){
      return false;
      state0=0;
    }
    uint256 divisor=10;
    uint256 h=5;
    uint256 state1=0;
    while(divisor>0){
      if(state1==0){
        if(divisor>5){
          state1=1;
        }else{
          state1=4;
        }
      }
      if(state1==1){
        if(h>2){
          state1=2;
        }
      }
      if(state1==2){
        h=h+2;
        state1=3;
      }
      if(state1==3){
        h=h+1;
        h=h+1;
        state1=5;
      }
      if(state1==4){
        h=h-1;
        state1=5;
      }
      if(state1==5){
        divisor=divisor-1;
        state1=0;
      }
    }
    uint256 state2=0;
    while(divisor>0){
      if(state2==0){
        if(divisor>5){
          state2=1;
        }else{
          state2=4;
        }
      }
      if(state2==1){
        if(h>2){
          state2=2;
        }
      }
      if(state2==2){
        h=h+2;
        state2=3;
      }
      if(state2==3){
        h=h+1;
        h=h+1;
        state2=5;
      }
      if(state2==4){
        h=h-1;
        state2=5;
      }
      if(state2==5){
        divisor=divisor-1;
        state2=0;
      }
    }
    return true;
  }
}
