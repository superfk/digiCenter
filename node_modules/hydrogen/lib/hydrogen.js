(function(undefined) {
    'use strict';

    var h, // public functions
        hasModule = (typeof exports !== 'undefined');

    function extend(target, props) {
        for(var key in props) {
            if (props.hasOwnProperty(key)) {
                target[key] = props[key];
            }
        }
    }

    function instantiate(obj, args) {
        function F() {
            return obj.apply(this, args);
        }
        F.prototype = obj.prototype;
        return new F();
    }

    function startsWithVowel(str) {
        if (!str) {
            return false;
        }
        var firstCh = str.charAt(0).toLowerCase();
        return ('a' == firstCh || 'e' == firstCh || 'i' == firstCh || 'o' == firstCh || 'u' == firstCh);
    }

    h = {

        create: function create(Obj, arg1, arg2) {
            var SuperObj,
                superInst,
                props;
            if (undefined === arg2) {
                props = arg1;
            } else {
                SuperObj = arg1;
                props = arg2;
            }

            if (SuperObj) {
                if ('function' === typeof SuperObj.makeInst) {
                    superInst = SuperObj.makeInst();
                } else {
                    superInst = new SuperObj();
                }
                Obj.prototype = superInst;
                Obj.prototype.super = {
                    constructor: SuperObj
                };
            }

            extend(Obj.prototype, props);

            Obj.makeInst = function makeInst() {
                return instantiate(Obj, arguments);
            };

            return h;
        },

        attach: function attach(Obj, closure) {
            if ('function' !== typeof closure) {
                throw new Error('closure is of type ' + (typeof closure) + ', expected to be a function');
            }

            Obj.makeInst = function makeInst() {
                var instance = instantiate(Obj, arguments);

                var closureProps = closure.call(instance);
                extend(instance, closureProps);

                return instance;
            };

            return h;
        },

        checkImpl: function checkImpl(impl, iDef) {
            if (iDef.type != typeof impl) {
                return 'Value is not a' + (startsWithVowel(iDef.type) ? 'n ' : ' ') + iDef.type;
            }

            if ('function' == iDef.type) {
                if (impl.length < iDef.minArity) {
                    return 'Function does not accept at least ' + iDef.minArity + ' parameter' +
                        (1 == iDef.minArity ? '' : 's');
                }
            } else if ('object' == iDef.type) {
                for (var key in iDef.contents) {
                    if (iDef.contents.hasOwnProperty(key)) {
                        var keyCheck = this.checkImpl(impl[key], iDef.contents[key]);
                        if (true !== keyCheck) {
                            return 'At key ["' + key + '"]: ' + keyCheck;
                        }
                    }
                }
            }

            return true;
        }

    };

    if (hasModule) {
        module.exports = h;
    } else {
        this.h = h;
    }

}).call(this);