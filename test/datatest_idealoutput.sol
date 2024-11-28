pragma solidity ^0.8.0;

contract Example {
    uint256 public x = getIntFunc(0);
    string public greeting = getStrFunc(0);
    address public owner = getAddrFunc(0);
    bool public isActive = getBoolFunc(0);

    function getIntFunc(uint256 index) internal view returns(uint256){
        return _integer_constant[index];
    }

    function getStrFunc(uint256 index) internal view returns(string storage){
        return _string_constant[index];
    }

    function getAddrFunc(uint256 index) internal view returns(address){
        return _address_constant[index];
    }

    function getBoolFunc(uint256 index) internal view returns(bool){
        return _bool_constant[index];
    }
    uint256[] private _integer_constant = [42, 45];
    string[] private _string_constant = ["hello", "hello"];
    address[] private _address_constant = [0x1234567890123456789012345678901234567890];
    bool[] private _bool_constant = [true, false];
/*
    uint256[] private _integer_constant = [42];
    string[] private _string_constant = ["hello"];
    address[] private _address_constant = [0x1234567890123456789012345678901234567890];
    bool[] private _bool_constant = [true];
*/
}
