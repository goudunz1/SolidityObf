// SPDX-License-Identifier: GPL-3.0

/**
 * @title grammar.sol
 * @author goudunz1
 * @notice Note that this file is not a fuzzing test on solc. What we're doing
 *         here is to test our tool by generating a solidity source that covers
 *         all features. Therefore, we don't test compilation errors.
 */

pragma solidity >=0.8.0 <0.9.0;

type num is uint256;

// library-definition
library Library0 {

    // string-literal
    string constant string0 = "\x27\x5c\u4ee5\u592a\x22\x0a"; // '\'\\以太"\n'

    // number-literal
    uint256 constant number0 = 0x9e3779b9 * 1000_0000 wei;

    // boolean-literal
    bool constant bool0 = false && true;

    // hex-string-literal
    bytes constant hex0 = hex"9e3779b9";

    // unicode-string-literal
    bytes constant unicode0 = unicode"智能合约"; // '\u667a\u80fd\u5408\u7ea6'

}

// interface-definition
interface Interface0 {

    function function0(uint256, uint256) external payable;

}

interface Interface1 {

    function function0(uint256, uint256) external payable;

}

abstract contract Base0 {

    // modifier-definition
    modifier modifier0(uint256 x, uint256 y) virtual {
        _;
    }

}

// contract-definition
contract Subclass0 is Interface0, Interface1, Base0 {

    // struct-definition
    struct struct0 {
        uint256 mem0;
        uint256 mem1;
        uint256 mem2;
    }

    // enum-definition
    enum Enum0 {
        ENUM0,
        ENUM1,
        ENUM2
    }

    // even-definition
    event Event0(uint256, uint256) anonymous;

    // error-definition
    error Error0(uint256, uint256);

    // immutable state variable
    address payable public immutable variable0 = payable(0x5B38Da6a701c568545dCfcB03FcB875f56beddC4);

    // transient state variable
    uint256 public transient variable1;

    uint256[8][8*8] private variable2;

    // constructor-definition
    constructor() { }

    // modifier-definition
    modifier modifier0(uint256 x, uint256 y) override (Base0) {
        assert(x != y);
        _;
    }

    // function-definition
    function function0(uint256 x, uint256 y)
    external payable Subclass0.modifier0(x, y)
    virtual override (Interface0, Interface1) {
        uint32 i = 0;
        do {
            i++;
            if (i > 5)
                break;
            else
                continue;
        } while (i < 10);
        revert Error0(x, y);
    }
    
    function function1(uint256[] calldata a) public {
        uint256[] memory b = a[1:];
        this.function0({y: (3*1), x: 1});
    }
}
