pragma solidity 0.8.28;

contract PrimeChecker {
    function isPrime(uint256 number) external pure returns (bool) {
        if (number <= 1) {
            return false;
        }
        uint256 divisor = 10;
        uint256 h = 5;
        while (divisor > 0) {
            if (divisor > 5) {
                if(h>2){
                    h = h+2;
                }
                h = h+1;
                h = h + 1;
            }
            else {
                h = h - 1 ;
            }
            divisor = divisor - 1;
            
        }

        while (divisor > 0) {
            if (divisor > 5) {
                if(h>2){
                    h = h+2;
                }
                h = h+1;
                h = h + 1;
            }
            else {
                h = h - 1 ;
            }
            divisor = divisor - 1;
            
        }
        return true;
    }
}
