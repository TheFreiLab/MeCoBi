(function(){const e=document.createElement("link").relList;if(e&&e.supports&&e.supports("modulepreload"))return;for(const r of document.querySelectorAll('link[rel="modulepreload"]'))i(r);new MutationObserver(r=>{for(const s of r)if(s.type==="childList")for(const o of s.addedNodes)o.tagName==="LINK"&&o.rel==="modulepreload"&&i(o)}).observe(document,{childList:!0,subtree:!0});function n(r){const s={};return r.integrity&&(s.integrity=r.integrity),r.referrerPolicy&&(s.referrerPolicy=r.referrerPolicy),r.crossOrigin==="use-credentials"?s.credentials="include":r.crossOrigin==="anonymous"?s.credentials="omit":s.credentials="same-origin",s}function i(r){if(r.ep)return;r.ep=!0;const s=n(r);fetch(r.href,s)}})();function a0(t){return t&&t.__esModule&&Object.prototype.hasOwnProperty.call(t,"default")?t.default:t}var ug={exports:{}},rc={},dg={exports:{}},nt={};/**
 * @license React
 * react.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var ta=Symbol.for("react.element"),l0=Symbol.for("react.portal"),c0=Symbol.for("react.fragment"),u0=Symbol.for("react.strict_mode"),d0=Symbol.for("react.profiler"),h0=Symbol.for("react.provider"),f0=Symbol.for("react.context"),p0=Symbol.for("react.forward_ref"),m0=Symbol.for("react.suspense"),g0=Symbol.for("react.memo"),_0=Symbol.for("react.lazy"),Df=Symbol.iterator;function v0(t){return t===null||typeof t!="object"?null:(t=Df&&t[Df]||t["@@iterator"],typeof t=="function"?t:null)}var hg={isMounted:function(){return!1},enqueueForceUpdate:function(){},enqueueReplaceState:function(){},enqueueSetState:function(){}},fg=Object.assign,pg={};function Zs(t,e,n){this.props=t,this.context=e,this.refs=pg,this.updater=n||hg}Zs.prototype.isReactComponent={};Zs.prototype.setState=function(t,e){if(typeof t!="object"&&typeof t!="function"&&t!=null)throw Error("setState(...): takes an object of state variables to update or a function which returns an object of state variables.");this.updater.enqueueSetState(this,t,e,"setState")};Zs.prototype.forceUpdate=function(t){this.updater.enqueueForceUpdate(this,t,"forceUpdate")};function mg(){}mg.prototype=Zs.prototype;function Th(t,e,n){this.props=t,this.context=e,this.refs=pg,this.updater=n||hg}var Ah=Th.prototype=new mg;Ah.constructor=Th;fg(Ah,Zs.prototype);Ah.isPureReactComponent=!0;var If=Array.isArray,gg=Object.prototype.hasOwnProperty,Ch={current:null},_g={key:!0,ref:!0,__self:!0,__source:!0};function vg(t,e,n){var i,r={},s=null,o=null;if(e!=null)for(i in e.ref!==void 0&&(o=e.ref),e.key!==void 0&&(s=""+e.key),e)gg.call(e,i)&&!_g.hasOwnProperty(i)&&(r[i]=e[i]);var a=arguments.length-2;if(a===1)r.children=n;else if(1<a){for(var l=Array(a),c=0;c<a;c++)l[c]=arguments[c+2];r.children=l}if(t&&t.defaultProps)for(i in a=t.defaultProps,a)r[i]===void 0&&(r[i]=a[i]);return{$$typeof:ta,type:t,key:s,ref:o,props:r,_owner:Ch.current}}function x0(t,e){return{$$typeof:ta,type:t.type,key:e,ref:t.ref,props:t.props,_owner:t._owner}}function bh(t){return typeof t=="object"&&t!==null&&t.$$typeof===ta}function y0(t){var e={"=":"=0",":":"=2"};return"$"+t.replace(/[=:]/g,function(n){return e[n]})}var Uf=/\/+/g;function Ac(t,e){return typeof t=="object"&&t!==null&&t.key!=null?y0(""+t.key):e.toString(36)}function rl(t,e,n,i,r){var s=typeof t;(s==="undefined"||s==="boolean")&&(t=null);var o=!1;if(t===null)o=!0;else switch(s){case"string":case"number":o=!0;break;case"object":switch(t.$$typeof){case ta:case l0:o=!0}}if(o)return o=t,r=r(o),t=i===""?"."+Ac(o,0):i,If(r)?(n="",t!=null&&(n=t.replace(Uf,"$&/")+"/"),rl(r,e,n,"",function(c){return c})):r!=null&&(bh(r)&&(r=x0(r,n+(!r.key||o&&o.key===r.key?"":(""+r.key).replace(Uf,"$&/")+"/")+t)),e.push(r)),1;if(o=0,i=i===""?".":i+":",If(t))for(var a=0;a<t.length;a++){s=t[a];var l=i+Ac(s,a);o+=rl(s,e,n,l,r)}else if(l=v0(t),typeof l=="function")for(t=l.call(t),a=0;!(s=t.next()).done;)s=s.value,l=i+Ac(s,a++),o+=rl(s,e,n,l,r);else if(s==="object")throw e=String(t),Error("Objects are not valid as a React child (found: "+(e==="[object Object]"?"object with keys {"+Object.keys(t).join(", ")+"}":e)+"). If you meant to render a collection of children, use an array instead.");return o}function pa(t,e,n){if(t==null)return t;var i=[],r=0;return rl(t,i,"","",function(s){return e.call(n,s,r++)}),i}function S0(t){if(t._status===-1){var e=t._result;e=e(),e.then(function(n){(t._status===0||t._status===-1)&&(t._status=1,t._result=n)},function(n){(t._status===0||t._status===-1)&&(t._status=2,t._result=n)}),t._status===-1&&(t._status=0,t._result=e)}if(t._status===1)return t._result.default;throw t._result}var on={current:null},sl={transition:null},M0={ReactCurrentDispatcher:on,ReactCurrentBatchConfig:sl,ReactCurrentOwner:Ch};function xg(){throw Error("act(...) is not supported in production builds of React.")}nt.Children={map:pa,forEach:function(t,e,n){pa(t,function(){e.apply(this,arguments)},n)},count:function(t){var e=0;return pa(t,function(){e++}),e},toArray:function(t){return pa(t,function(e){return e})||[]},only:function(t){if(!bh(t))throw Error("React.Children.only expected to receive a single React element child.");return t}};nt.Component=Zs;nt.Fragment=c0;nt.Profiler=d0;nt.PureComponent=Th;nt.StrictMode=u0;nt.Suspense=m0;nt.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED=M0;nt.act=xg;nt.cloneElement=function(t,e,n){if(t==null)throw Error("React.cloneElement(...): The argument must be a React element, but you passed "+t+".");var i=fg({},t.props),r=t.key,s=t.ref,o=t._owner;if(e!=null){if(e.ref!==void 0&&(s=e.ref,o=Ch.current),e.key!==void 0&&(r=""+e.key),t.type&&t.type.defaultProps)var a=t.type.defaultProps;for(l in e)gg.call(e,l)&&!_g.hasOwnProperty(l)&&(i[l]=e[l]===void 0&&a!==void 0?a[l]:e[l])}var l=arguments.length-2;if(l===1)i.children=n;else if(1<l){a=Array(l);for(var c=0;c<l;c++)a[c]=arguments[c+2];i.children=a}return{$$typeof:ta,type:t.type,key:r,ref:s,props:i,_owner:o}};nt.createContext=function(t){return t={$$typeof:f0,_currentValue:t,_currentValue2:t,_threadCount:0,Provider:null,Consumer:null,_defaultValue:null,_globalName:null},t.Provider={$$typeof:h0,_context:t},t.Consumer=t};nt.createElement=vg;nt.createFactory=function(t){var e=vg.bind(null,t);return e.type=t,e};nt.createRef=function(){return{current:null}};nt.forwardRef=function(t){return{$$typeof:p0,render:t}};nt.isValidElement=bh;nt.lazy=function(t){return{$$typeof:_0,_payload:{_status:-1,_result:t},_init:S0}};nt.memo=function(t,e){return{$$typeof:g0,type:t,compare:e===void 0?null:e}};nt.startTransition=function(t){var e=sl.transition;sl.transition={};try{t()}finally{sl.transition=e}};nt.unstable_act=xg;nt.useCallback=function(t,e){return on.current.useCallback(t,e)};nt.useContext=function(t){return on.current.useContext(t)};nt.useDebugValue=function(){};nt.useDeferredValue=function(t){return on.current.useDeferredValue(t)};nt.useEffect=function(t,e){return on.current.useEffect(t,e)};nt.useId=function(){return on.current.useId()};nt.useImperativeHandle=function(t,e,n){return on.current.useImperativeHandle(t,e,n)};nt.useInsertionEffect=function(t,e){return on.current.useInsertionEffect(t,e)};nt.useLayoutEffect=function(t,e){return on.current.useLayoutEffect(t,e)};nt.useMemo=function(t,e){return on.current.useMemo(t,e)};nt.useReducer=function(t,e,n){return on.current.useReducer(t,e,n)};nt.useRef=function(t){return on.current.useRef(t)};nt.useState=function(t){return on.current.useState(t)};nt.useSyncExternalStore=function(t,e,n){return on.current.useSyncExternalStore(t,e,n)};nt.useTransition=function(){return on.current.useTransition()};nt.version="18.3.1";dg.exports=nt;var Q=dg.exports;const E0=a0(Q);/**
 * @license React
 * react-jsx-runtime.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var w0=Q,T0=Symbol.for("react.element"),A0=Symbol.for("react.fragment"),C0=Object.prototype.hasOwnProperty,b0=w0.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner,R0={key:!0,ref:!0,__self:!0,__source:!0};function yg(t,e,n){var i,r={},s=null,o=null;n!==void 0&&(s=""+n),e.key!==void 0&&(s=""+e.key),e.ref!==void 0&&(o=e.ref);for(i in e)C0.call(e,i)&&!R0.hasOwnProperty(i)&&(r[i]=e[i]);if(t&&t.defaultProps)for(i in e=t.defaultProps,e)r[i]===void 0&&(r[i]=e[i]);return{$$typeof:T0,type:t,key:s,ref:o,props:r,_owner:b0.current}}rc.Fragment=A0;rc.jsx=yg;rc.jsxs=yg;ug.exports=rc;var y=ug.exports,Sg={exports:{}},Rn={},Mg={exports:{}},Eg={};/**
 * @license React
 * scheduler.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */(function(t){function e(N,j){var Z=N.length;N.push(j);e:for(;0<Z;){var fe=Z-1>>>1,_e=N[fe];if(0<r(_e,j))N[fe]=j,N[Z]=_e,Z=fe;else break e}}function n(N){return N.length===0?null:N[0]}function i(N){if(N.length===0)return null;var j=N[0],Z=N.pop();if(Z!==j){N[0]=Z;e:for(var fe=0,_e=N.length,Re=_e>>>1;fe<Re;){var I=2*(fe+1)-1,z=N[I],ie=I+1,le=N[ie];if(0>r(z,Z))ie<_e&&0>r(le,z)?(N[fe]=le,N[ie]=Z,fe=ie):(N[fe]=z,N[I]=Z,fe=I);else if(ie<_e&&0>r(le,Z))N[fe]=le,N[ie]=Z,fe=ie;else break e}}return j}function r(N,j){var Z=N.sortIndex-j.sortIndex;return Z!==0?Z:N.id-j.id}if(typeof performance=="object"&&typeof performance.now=="function"){var s=performance;t.unstable_now=function(){return s.now()}}else{var o=Date,a=o.now();t.unstable_now=function(){return o.now()-a}}var l=[],c=[],d=1,h=null,f=3,p=!1,g=!1,x=!1,m=typeof setTimeout=="function"?setTimeout:null,u=typeof clearTimeout=="function"?clearTimeout:null,_=typeof setImmediate<"u"?setImmediate:null;typeof navigator<"u"&&navigator.scheduling!==void 0&&navigator.scheduling.isInputPending!==void 0&&navigator.scheduling.isInputPending.bind(navigator.scheduling);function v(N){for(var j=n(c);j!==null;){if(j.callback===null)i(c);else if(j.startTime<=N)i(c),j.sortIndex=j.expirationTime,e(l,j);else break;j=n(c)}}function M(N){if(x=!1,v(N),!g)if(n(l)!==null)g=!0,V(R);else{var j=n(c);j!==null&&J(M,j.startTime-N)}}function R(N,j){g=!1,x&&(x=!1,u(P),P=-1),p=!0;var Z=f;try{for(v(j),h=n(l);h!==null&&(!(h.expirationTime>j)||N&&!D());){var fe=h.callback;if(typeof fe=="function"){h.callback=null,f=h.priorityLevel;var _e=fe(h.expirationTime<=j);j=t.unstable_now(),typeof _e=="function"?h.callback=_e:h===n(l)&&i(l),v(j)}else i(l);h=n(l)}if(h!==null)var Re=!0;else{var I=n(c);I!==null&&J(M,I.startTime-j),Re=!1}return Re}finally{h=null,f=Z,p=!1}}var C=!1,A=null,P=-1,E=5,S=-1;function D(){return!(t.unstable_now()-S<E)}function X(){if(A!==null){var N=t.unstable_now();S=N;var j=!0;try{j=A(!0,N)}finally{j?H():(C=!1,A=null)}}else C=!1}var H;if(typeof _=="function")H=function(){_(X)};else if(typeof MessageChannel<"u"){var U=new MessageChannel,Y=U.port2;U.port1.onmessage=X,H=function(){Y.postMessage(null)}}else H=function(){m(X,0)};function V(N){A=N,C||(C=!0,H())}function J(N,j){P=m(function(){N(t.unstable_now())},j)}t.unstable_IdlePriority=5,t.unstable_ImmediatePriority=1,t.unstable_LowPriority=4,t.unstable_NormalPriority=3,t.unstable_Profiling=null,t.unstable_UserBlockingPriority=2,t.unstable_cancelCallback=function(N){N.callback=null},t.unstable_continueExecution=function(){g||p||(g=!0,V(R))},t.unstable_forceFrameRate=function(N){0>N||125<N?console.error("forceFrameRate takes a positive int between 0 and 125, forcing frame rates higher than 125 fps is not supported"):E=0<N?Math.floor(1e3/N):5},t.unstable_getCurrentPriorityLevel=function(){return f},t.unstable_getFirstCallbackNode=function(){return n(l)},t.unstable_next=function(N){switch(f){case 1:case 2:case 3:var j=3;break;default:j=f}var Z=f;f=j;try{return N()}finally{f=Z}},t.unstable_pauseExecution=function(){},t.unstable_requestPaint=function(){},t.unstable_runWithPriority=function(N,j){switch(N){case 1:case 2:case 3:case 4:case 5:break;default:N=3}var Z=f;f=N;try{return j()}finally{f=Z}},t.unstable_scheduleCallback=function(N,j,Z){var fe=t.unstable_now();switch(typeof Z=="object"&&Z!==null?(Z=Z.delay,Z=typeof Z=="number"&&0<Z?fe+Z:fe):Z=fe,N){case 1:var _e=-1;break;case 2:_e=250;break;case 5:_e=1073741823;break;case 4:_e=1e4;break;default:_e=5e3}return _e=Z+_e,N={id:d++,callback:j,priorityLevel:N,startTime:Z,expirationTime:_e,sortIndex:-1},Z>fe?(N.sortIndex=Z,e(c,N),n(l)===null&&N===n(c)&&(x?(u(P),P=-1):x=!0,J(M,Z-fe))):(N.sortIndex=_e,e(l,N),g||p||(g=!0,V(R))),N},t.unstable_shouldYield=D,t.unstable_wrapCallback=function(N){var j=f;return function(){var Z=f;f=j;try{return N.apply(this,arguments)}finally{f=Z}}}})(Eg);Mg.exports=Eg;var P0=Mg.exports;/**
 * @license React
 * react-dom.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var L0=Q,bn=P0;function he(t){for(var e="https://reactjs.org/docs/error-decoder.html?invariant="+t,n=1;n<arguments.length;n++)e+="&args[]="+encodeURIComponent(arguments[n]);return"Minified React error #"+t+"; visit "+e+" for the full message or use the non-minified dev environment for full errors and additional helpful warnings."}var wg=new Set,Oo={};function Wr(t,e){Fs(t,e),Fs(t+"Capture",e)}function Fs(t,e){for(Oo[t]=e,t=0;t<e.length;t++)wg.add(e[t])}var Li=!(typeof window>"u"||typeof window.document>"u"||typeof window.document.createElement>"u"),ju=Object.prototype.hasOwnProperty,N0=/^[:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD][:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\-.0-9\u00B7\u0300-\u036F\u203F-\u2040]*$/,Of={},Ff={};function D0(t){return ju.call(Ff,t)?!0:ju.call(Of,t)?!1:N0.test(t)?Ff[t]=!0:(Of[t]=!0,!1)}function I0(t,e,n,i){if(n!==null&&n.type===0)return!1;switch(typeof e){case"function":case"symbol":return!0;case"boolean":return i?!1:n!==null?!n.acceptsBooleans:(t=t.toLowerCase().slice(0,5),t!=="data-"&&t!=="aria-");default:return!1}}function U0(t,e,n,i){if(e===null||typeof e>"u"||I0(t,e,n,i))return!0;if(i)return!1;if(n!==null)switch(n.type){case 3:return!e;case 4:return e===!1;case 5:return isNaN(e);case 6:return isNaN(e)||1>e}return!1}function an(t,e,n,i,r,s,o){this.acceptsBooleans=e===2||e===3||e===4,this.attributeName=i,this.attributeNamespace=r,this.mustUseProperty=n,this.propertyName=t,this.type=e,this.sanitizeURL=s,this.removeEmptyString=o}var $t={};"children dangerouslySetInnerHTML defaultValue defaultChecked innerHTML suppressContentEditableWarning suppressHydrationWarning style".split(" ").forEach(function(t){$t[t]=new an(t,0,!1,t,null,!1,!1)});[["acceptCharset","accept-charset"],["className","class"],["htmlFor","for"],["httpEquiv","http-equiv"]].forEach(function(t){var e=t[0];$t[e]=new an(e,1,!1,t[1],null,!1,!1)});["contentEditable","draggable","spellCheck","value"].forEach(function(t){$t[t]=new an(t,2,!1,t.toLowerCase(),null,!1,!1)});["autoReverse","externalResourcesRequired","focusable","preserveAlpha"].forEach(function(t){$t[t]=new an(t,2,!1,t,null,!1,!1)});"allowFullScreen async autoFocus autoPlay controls default defer disabled disablePictureInPicture disableRemotePlayback formNoValidate hidden loop noModule noValidate open playsInline readOnly required reversed scoped seamless itemScope".split(" ").forEach(function(t){$t[t]=new an(t,3,!1,t.toLowerCase(),null,!1,!1)});["checked","multiple","muted","selected"].forEach(function(t){$t[t]=new an(t,3,!0,t,null,!1,!1)});["capture","download"].forEach(function(t){$t[t]=new an(t,4,!1,t,null,!1,!1)});["cols","rows","size","span"].forEach(function(t){$t[t]=new an(t,6,!1,t,null,!1,!1)});["rowSpan","start"].forEach(function(t){$t[t]=new an(t,5,!1,t.toLowerCase(),null,!1,!1)});var Rh=/[\-:]([a-z])/g;function Ph(t){return t[1].toUpperCase()}"accent-height alignment-baseline arabic-form baseline-shift cap-height clip-path clip-rule color-interpolation color-interpolation-filters color-profile color-rendering dominant-baseline enable-background fill-opacity fill-rule flood-color flood-opacity font-family font-size font-size-adjust font-stretch font-style font-variant font-weight glyph-name glyph-orientation-horizontal glyph-orientation-vertical horiz-adv-x horiz-origin-x image-rendering letter-spacing lighting-color marker-end marker-mid marker-start overline-position overline-thickness paint-order panose-1 pointer-events rendering-intent shape-rendering stop-color stop-opacity strikethrough-position strikethrough-thickness stroke-dasharray stroke-dashoffset stroke-linecap stroke-linejoin stroke-miterlimit stroke-opacity stroke-width text-anchor text-decoration text-rendering underline-position underline-thickness unicode-bidi unicode-range units-per-em v-alphabetic v-hanging v-ideographic v-mathematical vector-effect vert-adv-y vert-origin-x vert-origin-y word-spacing writing-mode xmlns:xlink x-height".split(" ").forEach(function(t){var e=t.replace(Rh,Ph);$t[e]=new an(e,1,!1,t,null,!1,!1)});"xlink:actuate xlink:arcrole xlink:role xlink:show xlink:title xlink:type".split(" ").forEach(function(t){var e=t.replace(Rh,Ph);$t[e]=new an(e,1,!1,t,"http://www.w3.org/1999/xlink",!1,!1)});["xml:base","xml:lang","xml:space"].forEach(function(t){var e=t.replace(Rh,Ph);$t[e]=new an(e,1,!1,t,"http://www.w3.org/XML/1998/namespace",!1,!1)});["tabIndex","crossOrigin"].forEach(function(t){$t[t]=new an(t,1,!1,t.toLowerCase(),null,!1,!1)});$t.xlinkHref=new an("xlinkHref",1,!1,"xlink:href","http://www.w3.org/1999/xlink",!0,!1);["src","href","action","formAction"].forEach(function(t){$t[t]=new an(t,1,!1,t.toLowerCase(),null,!0,!0)});function Lh(t,e,n,i){var r=$t.hasOwnProperty(e)?$t[e]:null;(r!==null?r.type!==0:i||!(2<e.length)||e[0]!=="o"&&e[0]!=="O"||e[1]!=="n"&&e[1]!=="N")&&(U0(e,n,r,i)&&(n=null),i||r===null?D0(e)&&(n===null?t.removeAttribute(e):t.setAttribute(e,""+n)):r.mustUseProperty?t[r.propertyName]=n===null?r.type===3?!1:"":n:(e=r.attributeName,i=r.attributeNamespace,n===null?t.removeAttribute(e):(r=r.type,n=r===3||r===4&&n===!0?"":""+n,i?t.setAttributeNS(i,e,n):t.setAttribute(e,n))))}var Oi=L0.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED,ma=Symbol.for("react.element"),fs=Symbol.for("react.portal"),ps=Symbol.for("react.fragment"),Nh=Symbol.for("react.strict_mode"),Wu=Symbol.for("react.profiler"),Tg=Symbol.for("react.provider"),Ag=Symbol.for("react.context"),Dh=Symbol.for("react.forward_ref"),Xu=Symbol.for("react.suspense"),$u=Symbol.for("react.suspense_list"),Ih=Symbol.for("react.memo"),Xi=Symbol.for("react.lazy"),Cg=Symbol.for("react.offscreen"),kf=Symbol.iterator;function io(t){return t===null||typeof t!="object"?null:(t=kf&&t[kf]||t["@@iterator"],typeof t=="function"?t:null)}var Tt=Object.assign,Cc;function vo(t){if(Cc===void 0)try{throw Error()}catch(n){var e=n.stack.trim().match(/\n( *(at )?)/);Cc=e&&e[1]||""}return`
`+Cc+t}var bc=!1;function Rc(t,e){if(!t||bc)return"";bc=!0;var n=Error.prepareStackTrace;Error.prepareStackTrace=void 0;try{if(e)if(e=function(){throw Error()},Object.defineProperty(e.prototype,"props",{set:function(){throw Error()}}),typeof Reflect=="object"&&Reflect.construct){try{Reflect.construct(e,[])}catch(c){var i=c}Reflect.construct(t,[],e)}else{try{e.call()}catch(c){i=c}t.call(e.prototype)}else{try{throw Error()}catch(c){i=c}t()}}catch(c){if(c&&i&&typeof c.stack=="string"){for(var r=c.stack.split(`
`),s=i.stack.split(`
`),o=r.length-1,a=s.length-1;1<=o&&0<=a&&r[o]!==s[a];)a--;for(;1<=o&&0<=a;o--,a--)if(r[o]!==s[a]){if(o!==1||a!==1)do if(o--,a--,0>a||r[o]!==s[a]){var l=`
`+r[o].replace(" at new "," at ");return t.displayName&&l.includes("<anonymous>")&&(l=l.replace("<anonymous>",t.displayName)),l}while(1<=o&&0<=a);break}}}finally{bc=!1,Error.prepareStackTrace=n}return(t=t?t.displayName||t.name:"")?vo(t):""}function O0(t){switch(t.tag){case 5:return vo(t.type);case 16:return vo("Lazy");case 13:return vo("Suspense");case 19:return vo("SuspenseList");case 0:case 2:case 15:return t=Rc(t.type,!1),t;case 11:return t=Rc(t.type.render,!1),t;case 1:return t=Rc(t.type,!0),t;default:return""}}function Yu(t){if(t==null)return null;if(typeof t=="function")return t.displayName||t.name||null;if(typeof t=="string")return t;switch(t){case ps:return"Fragment";case fs:return"Portal";case Wu:return"Profiler";case Nh:return"StrictMode";case Xu:return"Suspense";case $u:return"SuspenseList"}if(typeof t=="object")switch(t.$$typeof){case Ag:return(t.displayName||"Context")+".Consumer";case Tg:return(t._context.displayName||"Context")+".Provider";case Dh:var e=t.render;return t=t.displayName,t||(t=e.displayName||e.name||"",t=t!==""?"ForwardRef("+t+")":"ForwardRef"),t;case Ih:return e=t.displayName||null,e!==null?e:Yu(t.type)||"Memo";case Xi:e=t._payload,t=t._init;try{return Yu(t(e))}catch{}}return null}function F0(t){var e=t.type;switch(t.tag){case 24:return"Cache";case 9:return(e.displayName||"Context")+".Consumer";case 10:return(e._context.displayName||"Context")+".Provider";case 18:return"DehydratedFragment";case 11:return t=e.render,t=t.displayName||t.name||"",e.displayName||(t!==""?"ForwardRef("+t+")":"ForwardRef");case 7:return"Fragment";case 5:return e;case 4:return"Portal";case 3:return"Root";case 6:return"Text";case 16:return Yu(e);case 8:return e===Nh?"StrictMode":"Mode";case 22:return"Offscreen";case 12:return"Profiler";case 21:return"Scope";case 13:return"Suspense";case 19:return"SuspenseList";case 25:return"TracingMarker";case 1:case 0:case 17:case 2:case 14:case 15:if(typeof e=="function")return e.displayName||e.name||null;if(typeof e=="string")return e}return null}function ur(t){switch(typeof t){case"boolean":case"number":case"string":case"undefined":return t;case"object":return t;default:return""}}function bg(t){var e=t.type;return(t=t.nodeName)&&t.toLowerCase()==="input"&&(e==="checkbox"||e==="radio")}function k0(t){var e=bg(t)?"checked":"value",n=Object.getOwnPropertyDescriptor(t.constructor.prototype,e),i=""+t[e];if(!t.hasOwnProperty(e)&&typeof n<"u"&&typeof n.get=="function"&&typeof n.set=="function"){var r=n.get,s=n.set;return Object.defineProperty(t,e,{configurable:!0,get:function(){return r.call(this)},set:function(o){i=""+o,s.call(this,o)}}),Object.defineProperty(t,e,{enumerable:n.enumerable}),{getValue:function(){return i},setValue:function(o){i=""+o},stopTracking:function(){t._valueTracker=null,delete t[e]}}}}function ga(t){t._valueTracker||(t._valueTracker=k0(t))}function Rg(t){if(!t)return!1;var e=t._valueTracker;if(!e)return!0;var n=e.getValue(),i="";return t&&(i=bg(t)?t.checked?"true":"false":t.value),t=i,t!==n?(e.setValue(t),!0):!1}function Al(t){if(t=t||(typeof document<"u"?document:void 0),typeof t>"u")return null;try{return t.activeElement||t.body}catch{return t.body}}function qu(t,e){var n=e.checked;return Tt({},e,{defaultChecked:void 0,defaultValue:void 0,value:void 0,checked:n??t._wrapperState.initialChecked})}function Bf(t,e){var n=e.defaultValue==null?"":e.defaultValue,i=e.checked!=null?e.checked:e.defaultChecked;n=ur(e.value!=null?e.value:n),t._wrapperState={initialChecked:i,initialValue:n,controlled:e.type==="checkbox"||e.type==="radio"?e.checked!=null:e.value!=null}}function Pg(t,e){e=e.checked,e!=null&&Lh(t,"checked",e,!1)}function Ku(t,e){Pg(t,e);var n=ur(e.value),i=e.type;if(n!=null)i==="number"?(n===0&&t.value===""||t.value!=n)&&(t.value=""+n):t.value!==""+n&&(t.value=""+n);else if(i==="submit"||i==="reset"){t.removeAttribute("value");return}e.hasOwnProperty("value")?Zu(t,e.type,n):e.hasOwnProperty("defaultValue")&&Zu(t,e.type,ur(e.defaultValue)),e.checked==null&&e.defaultChecked!=null&&(t.defaultChecked=!!e.defaultChecked)}function zf(t,e,n){if(e.hasOwnProperty("value")||e.hasOwnProperty("defaultValue")){var i=e.type;if(!(i!=="submit"&&i!=="reset"||e.value!==void 0&&e.value!==null))return;e=""+t._wrapperState.initialValue,n||e===t.value||(t.value=e),t.defaultValue=e}n=t.name,n!==""&&(t.name=""),t.defaultChecked=!!t._wrapperState.initialChecked,n!==""&&(t.name=n)}function Zu(t,e,n){(e!=="number"||Al(t.ownerDocument)!==t)&&(n==null?t.defaultValue=""+t._wrapperState.initialValue:t.defaultValue!==""+n&&(t.defaultValue=""+n))}var xo=Array.isArray;function Cs(t,e,n,i){if(t=t.options,e){e={};for(var r=0;r<n.length;r++)e["$"+n[r]]=!0;for(n=0;n<t.length;n++)r=e.hasOwnProperty("$"+t[n].value),t[n].selected!==r&&(t[n].selected=r),r&&i&&(t[n].defaultSelected=!0)}else{for(n=""+ur(n),e=null,r=0;r<t.length;r++){if(t[r].value===n){t[r].selected=!0,i&&(t[r].defaultSelected=!0);return}e!==null||t[r].disabled||(e=t[r])}e!==null&&(e.selected=!0)}}function Ju(t,e){if(e.dangerouslySetInnerHTML!=null)throw Error(he(91));return Tt({},e,{value:void 0,defaultValue:void 0,children:""+t._wrapperState.initialValue})}function Hf(t,e){var n=e.value;if(n==null){if(n=e.children,e=e.defaultValue,n!=null){if(e!=null)throw Error(he(92));if(xo(n)){if(1<n.length)throw Error(he(93));n=n[0]}e=n}e==null&&(e=""),n=e}t._wrapperState={initialValue:ur(n)}}function Lg(t,e){var n=ur(e.value),i=ur(e.defaultValue);n!=null&&(n=""+n,n!==t.value&&(t.value=n),e.defaultValue==null&&t.defaultValue!==n&&(t.defaultValue=n)),i!=null&&(t.defaultValue=""+i)}function Vf(t){var e=t.textContent;e===t._wrapperState.initialValue&&e!==""&&e!==null&&(t.value=e)}function Ng(t){switch(t){case"svg":return"http://www.w3.org/2000/svg";case"math":return"http://www.w3.org/1998/Math/MathML";default:return"http://www.w3.org/1999/xhtml"}}function Qu(t,e){return t==null||t==="http://www.w3.org/1999/xhtml"?Ng(e):t==="http://www.w3.org/2000/svg"&&e==="foreignObject"?"http://www.w3.org/1999/xhtml":t}var _a,Dg=function(t){return typeof MSApp<"u"&&MSApp.execUnsafeLocalFunction?function(e,n,i,r){MSApp.execUnsafeLocalFunction(function(){return t(e,n,i,r)})}:t}(function(t,e){if(t.namespaceURI!=="http://www.w3.org/2000/svg"||"innerHTML"in t)t.innerHTML=e;else{for(_a=_a||document.createElement("div"),_a.innerHTML="<svg>"+e.valueOf().toString()+"</svg>",e=_a.firstChild;t.firstChild;)t.removeChild(t.firstChild);for(;e.firstChild;)t.appendChild(e.firstChild)}});function Fo(t,e){if(e){var n=t.firstChild;if(n&&n===t.lastChild&&n.nodeType===3){n.nodeValue=e;return}}t.textContent=e}var wo={animationIterationCount:!0,aspectRatio:!0,borderImageOutset:!0,borderImageSlice:!0,borderImageWidth:!0,boxFlex:!0,boxFlexGroup:!0,boxOrdinalGroup:!0,columnCount:!0,columns:!0,flex:!0,flexGrow:!0,flexPositive:!0,flexShrink:!0,flexNegative:!0,flexOrder:!0,gridArea:!0,gridRow:!0,gridRowEnd:!0,gridRowSpan:!0,gridRowStart:!0,gridColumn:!0,gridColumnEnd:!0,gridColumnSpan:!0,gridColumnStart:!0,fontWeight:!0,lineClamp:!0,lineHeight:!0,opacity:!0,order:!0,orphans:!0,tabSize:!0,widows:!0,zIndex:!0,zoom:!0,fillOpacity:!0,floodOpacity:!0,stopOpacity:!0,strokeDasharray:!0,strokeDashoffset:!0,strokeMiterlimit:!0,strokeOpacity:!0,strokeWidth:!0},B0=["Webkit","ms","Moz","O"];Object.keys(wo).forEach(function(t){B0.forEach(function(e){e=e+t.charAt(0).toUpperCase()+t.substring(1),wo[e]=wo[t]})});function Ig(t,e,n){return e==null||typeof e=="boolean"||e===""?"":n||typeof e!="number"||e===0||wo.hasOwnProperty(t)&&wo[t]?(""+e).trim():e+"px"}function Ug(t,e){t=t.style;for(var n in e)if(e.hasOwnProperty(n)){var i=n.indexOf("--")===0,r=Ig(n,e[n],i);n==="float"&&(n="cssFloat"),i?t.setProperty(n,r):t[n]=r}}var z0=Tt({menuitem:!0},{area:!0,base:!0,br:!0,col:!0,embed:!0,hr:!0,img:!0,input:!0,keygen:!0,link:!0,meta:!0,param:!0,source:!0,track:!0,wbr:!0});function ed(t,e){if(e){if(z0[t]&&(e.children!=null||e.dangerouslySetInnerHTML!=null))throw Error(he(137,t));if(e.dangerouslySetInnerHTML!=null){if(e.children!=null)throw Error(he(60));if(typeof e.dangerouslySetInnerHTML!="object"||!("__html"in e.dangerouslySetInnerHTML))throw Error(he(61))}if(e.style!=null&&typeof e.style!="object")throw Error(he(62))}}function td(t,e){if(t.indexOf("-")===-1)return typeof e.is=="string";switch(t){case"annotation-xml":case"color-profile":case"font-face":case"font-face-src":case"font-face-uri":case"font-face-format":case"font-face-name":case"missing-glyph":return!1;default:return!0}}var nd=null;function Uh(t){return t=t.target||t.srcElement||window,t.correspondingUseElement&&(t=t.correspondingUseElement),t.nodeType===3?t.parentNode:t}var id=null,bs=null,Rs=null;function Gf(t){if(t=ra(t)){if(typeof id!="function")throw Error(he(280));var e=t.stateNode;e&&(e=cc(e),id(t.stateNode,t.type,e))}}function Og(t){bs?Rs?Rs.push(t):Rs=[t]:bs=t}function Fg(){if(bs){var t=bs,e=Rs;if(Rs=bs=null,Gf(t),e)for(t=0;t<e.length;t++)Gf(e[t])}}function kg(t,e){return t(e)}function Bg(){}var Pc=!1;function zg(t,e,n){if(Pc)return t(e,n);Pc=!0;try{return kg(t,e,n)}finally{Pc=!1,(bs!==null||Rs!==null)&&(Bg(),Fg())}}function ko(t,e){var n=t.stateNode;if(n===null)return null;var i=cc(n);if(i===null)return null;n=i[e];e:switch(e){case"onClick":case"onClickCapture":case"onDoubleClick":case"onDoubleClickCapture":case"onMouseDown":case"onMouseDownCapture":case"onMouseMove":case"onMouseMoveCapture":case"onMouseUp":case"onMouseUpCapture":case"onMouseEnter":(i=!i.disabled)||(t=t.type,i=!(t==="button"||t==="input"||t==="select"||t==="textarea")),t=!i;break e;default:t=!1}if(t)return null;if(n&&typeof n!="function")throw Error(he(231,e,typeof n));return n}var rd=!1;if(Li)try{var ro={};Object.defineProperty(ro,"passive",{get:function(){rd=!0}}),window.addEventListener("test",ro,ro),window.removeEventListener("test",ro,ro)}catch{rd=!1}function H0(t,e,n,i,r,s,o,a,l){var c=Array.prototype.slice.call(arguments,3);try{e.apply(n,c)}catch(d){this.onError(d)}}var To=!1,Cl=null,bl=!1,sd=null,V0={onError:function(t){To=!0,Cl=t}};function G0(t,e,n,i,r,s,o,a,l){To=!1,Cl=null,H0.apply(V0,arguments)}function j0(t,e,n,i,r,s,o,a,l){if(G0.apply(this,arguments),To){if(To){var c=Cl;To=!1,Cl=null}else throw Error(he(198));bl||(bl=!0,sd=c)}}function Xr(t){var e=t,n=t;if(t.alternate)for(;e.return;)e=e.return;else{t=e;do e=t,e.flags&4098&&(n=e.return),t=e.return;while(t)}return e.tag===3?n:null}function Hg(t){if(t.tag===13){var e=t.memoizedState;if(e===null&&(t=t.alternate,t!==null&&(e=t.memoizedState)),e!==null)return e.dehydrated}return null}function jf(t){if(Xr(t)!==t)throw Error(he(188))}function W0(t){var e=t.alternate;if(!e){if(e=Xr(t),e===null)throw Error(he(188));return e!==t?null:t}for(var n=t,i=e;;){var r=n.return;if(r===null)break;var s=r.alternate;if(s===null){if(i=r.return,i!==null){n=i;continue}break}if(r.child===s.child){for(s=r.child;s;){if(s===n)return jf(r),t;if(s===i)return jf(r),e;s=s.sibling}throw Error(he(188))}if(n.return!==i.return)n=r,i=s;else{for(var o=!1,a=r.child;a;){if(a===n){o=!0,n=r,i=s;break}if(a===i){o=!0,i=r,n=s;break}a=a.sibling}if(!o){for(a=s.child;a;){if(a===n){o=!0,n=s,i=r;break}if(a===i){o=!0,i=s,n=r;break}a=a.sibling}if(!o)throw Error(he(189))}}if(n.alternate!==i)throw Error(he(190))}if(n.tag!==3)throw Error(he(188));return n.stateNode.current===n?t:e}function Vg(t){return t=W0(t),t!==null?Gg(t):null}function Gg(t){if(t.tag===5||t.tag===6)return t;for(t=t.child;t!==null;){var e=Gg(t);if(e!==null)return e;t=t.sibling}return null}var jg=bn.unstable_scheduleCallback,Wf=bn.unstable_cancelCallback,X0=bn.unstable_shouldYield,$0=bn.unstable_requestPaint,Pt=bn.unstable_now,Y0=bn.unstable_getCurrentPriorityLevel,Oh=bn.unstable_ImmediatePriority,Wg=bn.unstable_UserBlockingPriority,Rl=bn.unstable_NormalPriority,q0=bn.unstable_LowPriority,Xg=bn.unstable_IdlePriority,sc=null,ci=null;function K0(t){if(ci&&typeof ci.onCommitFiberRoot=="function")try{ci.onCommitFiberRoot(sc,t,void 0,(t.current.flags&128)===128)}catch{}}var ei=Math.clz32?Math.clz32:Q0,Z0=Math.log,J0=Math.LN2;function Q0(t){return t>>>=0,t===0?32:31-(Z0(t)/J0|0)|0}var va=64,xa=4194304;function yo(t){switch(t&-t){case 1:return 1;case 2:return 2;case 4:return 4;case 8:return 8;case 16:return 16;case 32:return 32;case 64:case 128:case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:case 262144:case 524288:case 1048576:case 2097152:return t&4194240;case 4194304:case 8388608:case 16777216:case 33554432:case 67108864:return t&130023424;case 134217728:return 134217728;case 268435456:return 268435456;case 536870912:return 536870912;case 1073741824:return 1073741824;default:return t}}function Pl(t,e){var n=t.pendingLanes;if(n===0)return 0;var i=0,r=t.suspendedLanes,s=t.pingedLanes,o=n&268435455;if(o!==0){var a=o&~r;a!==0?i=yo(a):(s&=o,s!==0&&(i=yo(s)))}else o=n&~r,o!==0?i=yo(o):s!==0&&(i=yo(s));if(i===0)return 0;if(e!==0&&e!==i&&!(e&r)&&(r=i&-i,s=e&-e,r>=s||r===16&&(s&4194240)!==0))return e;if(i&4&&(i|=n&16),e=t.entangledLanes,e!==0)for(t=t.entanglements,e&=i;0<e;)n=31-ei(e),r=1<<n,i|=t[n],e&=~r;return i}function ex(t,e){switch(t){case 1:case 2:case 4:return e+250;case 8:case 16:case 32:case 64:case 128:case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:case 262144:case 524288:case 1048576:case 2097152:return e+5e3;case 4194304:case 8388608:case 16777216:case 33554432:case 67108864:return-1;case 134217728:case 268435456:case 536870912:case 1073741824:return-1;default:return-1}}function tx(t,e){for(var n=t.suspendedLanes,i=t.pingedLanes,r=t.expirationTimes,s=t.pendingLanes;0<s;){var o=31-ei(s),a=1<<o,l=r[o];l===-1?(!(a&n)||a&i)&&(r[o]=ex(a,e)):l<=e&&(t.expiredLanes|=a),s&=~a}}function od(t){return t=t.pendingLanes&-1073741825,t!==0?t:t&1073741824?1073741824:0}function $g(){var t=va;return va<<=1,!(va&4194240)&&(va=64),t}function Lc(t){for(var e=[],n=0;31>n;n++)e.push(t);return e}function na(t,e,n){t.pendingLanes|=e,e!==536870912&&(t.suspendedLanes=0,t.pingedLanes=0),t=t.eventTimes,e=31-ei(e),t[e]=n}function nx(t,e){var n=t.pendingLanes&~e;t.pendingLanes=e,t.suspendedLanes=0,t.pingedLanes=0,t.expiredLanes&=e,t.mutableReadLanes&=e,t.entangledLanes&=e,e=t.entanglements;var i=t.eventTimes;for(t=t.expirationTimes;0<n;){var r=31-ei(n),s=1<<r;e[r]=0,i[r]=-1,t[r]=-1,n&=~s}}function Fh(t,e){var n=t.entangledLanes|=e;for(t=t.entanglements;n;){var i=31-ei(n),r=1<<i;r&e|t[i]&e&&(t[i]|=e),n&=~r}}var ht=0;function Yg(t){return t&=-t,1<t?4<t?t&268435455?16:536870912:4:1}var qg,kh,Kg,Zg,Jg,ad=!1,ya=[],er=null,tr=null,nr=null,Bo=new Map,zo=new Map,qi=[],ix="mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset submit".split(" ");function Xf(t,e){switch(t){case"focusin":case"focusout":er=null;break;case"dragenter":case"dragleave":tr=null;break;case"mouseover":case"mouseout":nr=null;break;case"pointerover":case"pointerout":Bo.delete(e.pointerId);break;case"gotpointercapture":case"lostpointercapture":zo.delete(e.pointerId)}}function so(t,e,n,i,r,s){return t===null||t.nativeEvent!==s?(t={blockedOn:e,domEventName:n,eventSystemFlags:i,nativeEvent:s,targetContainers:[r]},e!==null&&(e=ra(e),e!==null&&kh(e)),t):(t.eventSystemFlags|=i,e=t.targetContainers,r!==null&&e.indexOf(r)===-1&&e.push(r),t)}function rx(t,e,n,i,r){switch(e){case"focusin":return er=so(er,t,e,n,i,r),!0;case"dragenter":return tr=so(tr,t,e,n,i,r),!0;case"mouseover":return nr=so(nr,t,e,n,i,r),!0;case"pointerover":var s=r.pointerId;return Bo.set(s,so(Bo.get(s)||null,t,e,n,i,r)),!0;case"gotpointercapture":return s=r.pointerId,zo.set(s,so(zo.get(s)||null,t,e,n,i,r)),!0}return!1}function Qg(t){var e=Pr(t.target);if(e!==null){var n=Xr(e);if(n!==null){if(e=n.tag,e===13){if(e=Hg(n),e!==null){t.blockedOn=e,Jg(t.priority,function(){Kg(n)});return}}else if(e===3&&n.stateNode.current.memoizedState.isDehydrated){t.blockedOn=n.tag===3?n.stateNode.containerInfo:null;return}}}t.blockedOn=null}function ol(t){if(t.blockedOn!==null)return!1;for(var e=t.targetContainers;0<e.length;){var n=ld(t.domEventName,t.eventSystemFlags,e[0],t.nativeEvent);if(n===null){n=t.nativeEvent;var i=new n.constructor(n.type,n);nd=i,n.target.dispatchEvent(i),nd=null}else return e=ra(n),e!==null&&kh(e),t.blockedOn=n,!1;e.shift()}return!0}function $f(t,e,n){ol(t)&&n.delete(e)}function sx(){ad=!1,er!==null&&ol(er)&&(er=null),tr!==null&&ol(tr)&&(tr=null),nr!==null&&ol(nr)&&(nr=null),Bo.forEach($f),zo.forEach($f)}function oo(t,e){t.blockedOn===e&&(t.blockedOn=null,ad||(ad=!0,bn.unstable_scheduleCallback(bn.unstable_NormalPriority,sx)))}function Ho(t){function e(r){return oo(r,t)}if(0<ya.length){oo(ya[0],t);for(var n=1;n<ya.length;n++){var i=ya[n];i.blockedOn===t&&(i.blockedOn=null)}}for(er!==null&&oo(er,t),tr!==null&&oo(tr,t),nr!==null&&oo(nr,t),Bo.forEach(e),zo.forEach(e),n=0;n<qi.length;n++)i=qi[n],i.blockedOn===t&&(i.blockedOn=null);for(;0<qi.length&&(n=qi[0],n.blockedOn===null);)Qg(n),n.blockedOn===null&&qi.shift()}var Ps=Oi.ReactCurrentBatchConfig,Ll=!0;function ox(t,e,n,i){var r=ht,s=Ps.transition;Ps.transition=null;try{ht=1,Bh(t,e,n,i)}finally{ht=r,Ps.transition=s}}function ax(t,e,n,i){var r=ht,s=Ps.transition;Ps.transition=null;try{ht=4,Bh(t,e,n,i)}finally{ht=r,Ps.transition=s}}function Bh(t,e,n,i){if(Ll){var r=ld(t,e,n,i);if(r===null)Hc(t,e,i,Nl,n),Xf(t,i);else if(rx(r,t,e,n,i))i.stopPropagation();else if(Xf(t,i),e&4&&-1<ix.indexOf(t)){for(;r!==null;){var s=ra(r);if(s!==null&&qg(s),s=ld(t,e,n,i),s===null&&Hc(t,e,i,Nl,n),s===r)break;r=s}r!==null&&i.stopPropagation()}else Hc(t,e,i,null,n)}}var Nl=null;function ld(t,e,n,i){if(Nl=null,t=Uh(i),t=Pr(t),t!==null)if(e=Xr(t),e===null)t=null;else if(n=e.tag,n===13){if(t=Hg(e),t!==null)return t;t=null}else if(n===3){if(e.stateNode.current.memoizedState.isDehydrated)return e.tag===3?e.stateNode.containerInfo:null;t=null}else e!==t&&(t=null);return Nl=t,null}function e_(t){switch(t){case"cancel":case"click":case"close":case"contextmenu":case"copy":case"cut":case"auxclick":case"dblclick":case"dragend":case"dragstart":case"drop":case"focusin":case"focusout":case"input":case"invalid":case"keydown":case"keypress":case"keyup":case"mousedown":case"mouseup":case"paste":case"pause":case"play":case"pointercancel":case"pointerdown":case"pointerup":case"ratechange":case"reset":case"resize":case"seeked":case"submit":case"touchcancel":case"touchend":case"touchstart":case"volumechange":case"change":case"selectionchange":case"textInput":case"compositionstart":case"compositionend":case"compositionupdate":case"beforeblur":case"afterblur":case"beforeinput":case"blur":case"fullscreenchange":case"focus":case"hashchange":case"popstate":case"select":case"selectstart":return 1;case"drag":case"dragenter":case"dragexit":case"dragleave":case"dragover":case"mousemove":case"mouseout":case"mouseover":case"pointermove":case"pointerout":case"pointerover":case"scroll":case"toggle":case"touchmove":case"wheel":case"mouseenter":case"mouseleave":case"pointerenter":case"pointerleave":return 4;case"message":switch(Y0()){case Oh:return 1;case Wg:return 4;case Rl:case q0:return 16;case Xg:return 536870912;default:return 16}default:return 16}}var Ji=null,zh=null,al=null;function t_(){if(al)return al;var t,e=zh,n=e.length,i,r="value"in Ji?Ji.value:Ji.textContent,s=r.length;for(t=0;t<n&&e[t]===r[t];t++);var o=n-t;for(i=1;i<=o&&e[n-i]===r[s-i];i++);return al=r.slice(t,1<i?1-i:void 0)}function ll(t){var e=t.keyCode;return"charCode"in t?(t=t.charCode,t===0&&e===13&&(t=13)):t=e,t===10&&(t=13),32<=t||t===13?t:0}function Sa(){return!0}function Yf(){return!1}function Pn(t){function e(n,i,r,s,o){this._reactName=n,this._targetInst=r,this.type=i,this.nativeEvent=s,this.target=o,this.currentTarget=null;for(var a in t)t.hasOwnProperty(a)&&(n=t[a],this[a]=n?n(s):s[a]);return this.isDefaultPrevented=(s.defaultPrevented!=null?s.defaultPrevented:s.returnValue===!1)?Sa:Yf,this.isPropagationStopped=Yf,this}return Tt(e.prototype,{preventDefault:function(){this.defaultPrevented=!0;var n=this.nativeEvent;n&&(n.preventDefault?n.preventDefault():typeof n.returnValue!="unknown"&&(n.returnValue=!1),this.isDefaultPrevented=Sa)},stopPropagation:function(){var n=this.nativeEvent;n&&(n.stopPropagation?n.stopPropagation():typeof n.cancelBubble!="unknown"&&(n.cancelBubble=!0),this.isPropagationStopped=Sa)},persist:function(){},isPersistent:Sa}),e}var Js={eventPhase:0,bubbles:0,cancelable:0,timeStamp:function(t){return t.timeStamp||Date.now()},defaultPrevented:0,isTrusted:0},Hh=Pn(Js),ia=Tt({},Js,{view:0,detail:0}),lx=Pn(ia),Nc,Dc,ao,oc=Tt({},ia,{screenX:0,screenY:0,clientX:0,clientY:0,pageX:0,pageY:0,ctrlKey:0,shiftKey:0,altKey:0,metaKey:0,getModifierState:Vh,button:0,buttons:0,relatedTarget:function(t){return t.relatedTarget===void 0?t.fromElement===t.srcElement?t.toElement:t.fromElement:t.relatedTarget},movementX:function(t){return"movementX"in t?t.movementX:(t!==ao&&(ao&&t.type==="mousemove"?(Nc=t.screenX-ao.screenX,Dc=t.screenY-ao.screenY):Dc=Nc=0,ao=t),Nc)},movementY:function(t){return"movementY"in t?t.movementY:Dc}}),qf=Pn(oc),cx=Tt({},oc,{dataTransfer:0}),ux=Pn(cx),dx=Tt({},ia,{relatedTarget:0}),Ic=Pn(dx),hx=Tt({},Js,{animationName:0,elapsedTime:0,pseudoElement:0}),fx=Pn(hx),px=Tt({},Js,{clipboardData:function(t){return"clipboardData"in t?t.clipboardData:window.clipboardData}}),mx=Pn(px),gx=Tt({},Js,{data:0}),Kf=Pn(gx),_x={Esc:"Escape",Spacebar:" ",Left:"ArrowLeft",Up:"ArrowUp",Right:"ArrowRight",Down:"ArrowDown",Del:"Delete",Win:"OS",Menu:"ContextMenu",Apps:"ContextMenu",Scroll:"ScrollLock",MozPrintableKey:"Unidentified"},vx={8:"Backspace",9:"Tab",12:"Clear",13:"Enter",16:"Shift",17:"Control",18:"Alt",19:"Pause",20:"CapsLock",27:"Escape",32:" ",33:"PageUp",34:"PageDown",35:"End",36:"Home",37:"ArrowLeft",38:"ArrowUp",39:"ArrowRight",40:"ArrowDown",45:"Insert",46:"Delete",112:"F1",113:"F2",114:"F3",115:"F4",116:"F5",117:"F6",118:"F7",119:"F8",120:"F9",121:"F10",122:"F11",123:"F12",144:"NumLock",145:"ScrollLock",224:"Meta"},xx={Alt:"altKey",Control:"ctrlKey",Meta:"metaKey",Shift:"shiftKey"};function yx(t){var e=this.nativeEvent;return e.getModifierState?e.getModifierState(t):(t=xx[t])?!!e[t]:!1}function Vh(){return yx}var Sx=Tt({},ia,{key:function(t){if(t.key){var e=_x[t.key]||t.key;if(e!=="Unidentified")return e}return t.type==="keypress"?(t=ll(t),t===13?"Enter":String.fromCharCode(t)):t.type==="keydown"||t.type==="keyup"?vx[t.keyCode]||"Unidentified":""},code:0,location:0,ctrlKey:0,shiftKey:0,altKey:0,metaKey:0,repeat:0,locale:0,getModifierState:Vh,charCode:function(t){return t.type==="keypress"?ll(t):0},keyCode:function(t){return t.type==="keydown"||t.type==="keyup"?t.keyCode:0},which:function(t){return t.type==="keypress"?ll(t):t.type==="keydown"||t.type==="keyup"?t.keyCode:0}}),Mx=Pn(Sx),Ex=Tt({},oc,{pointerId:0,width:0,height:0,pressure:0,tangentialPressure:0,tiltX:0,tiltY:0,twist:0,pointerType:0,isPrimary:0}),Zf=Pn(Ex),wx=Tt({},ia,{touches:0,targetTouches:0,changedTouches:0,altKey:0,metaKey:0,ctrlKey:0,shiftKey:0,getModifierState:Vh}),Tx=Pn(wx),Ax=Tt({},Js,{propertyName:0,elapsedTime:0,pseudoElement:0}),Cx=Pn(Ax),bx=Tt({},oc,{deltaX:function(t){return"deltaX"in t?t.deltaX:"wheelDeltaX"in t?-t.wheelDeltaX:0},deltaY:function(t){return"deltaY"in t?t.deltaY:"wheelDeltaY"in t?-t.wheelDeltaY:"wheelDelta"in t?-t.wheelDelta:0},deltaZ:0,deltaMode:0}),Rx=Pn(bx),Px=[9,13,27,32],Gh=Li&&"CompositionEvent"in window,Ao=null;Li&&"documentMode"in document&&(Ao=document.documentMode);var Lx=Li&&"TextEvent"in window&&!Ao,n_=Li&&(!Gh||Ao&&8<Ao&&11>=Ao),Jf=" ",Qf=!1;function i_(t,e){switch(t){case"keyup":return Px.indexOf(e.keyCode)!==-1;case"keydown":return e.keyCode!==229;case"keypress":case"mousedown":case"focusout":return!0;default:return!1}}function r_(t){return t=t.detail,typeof t=="object"&&"data"in t?t.data:null}var ms=!1;function Nx(t,e){switch(t){case"compositionend":return r_(e);case"keypress":return e.which!==32?null:(Qf=!0,Jf);case"textInput":return t=e.data,t===Jf&&Qf?null:t;default:return null}}function Dx(t,e){if(ms)return t==="compositionend"||!Gh&&i_(t,e)?(t=t_(),al=zh=Ji=null,ms=!1,t):null;switch(t){case"paste":return null;case"keypress":if(!(e.ctrlKey||e.altKey||e.metaKey)||e.ctrlKey&&e.altKey){if(e.char&&1<e.char.length)return e.char;if(e.which)return String.fromCharCode(e.which)}return null;case"compositionend":return n_&&e.locale!=="ko"?null:e.data;default:return null}}var Ix={color:!0,date:!0,datetime:!0,"datetime-local":!0,email:!0,month:!0,number:!0,password:!0,range:!0,search:!0,tel:!0,text:!0,time:!0,url:!0,week:!0};function ep(t){var e=t&&t.nodeName&&t.nodeName.toLowerCase();return e==="input"?!!Ix[t.type]:e==="textarea"}function s_(t,e,n,i){Og(i),e=Dl(e,"onChange"),0<e.length&&(n=new Hh("onChange","change",null,n,i),t.push({event:n,listeners:e}))}var Co=null,Vo=null;function Ux(t){g_(t,0)}function ac(t){var e=vs(t);if(Rg(e))return t}function Ox(t,e){if(t==="change")return e}var o_=!1;if(Li){var Uc;if(Li){var Oc="oninput"in document;if(!Oc){var tp=document.createElement("div");tp.setAttribute("oninput","return;"),Oc=typeof tp.oninput=="function"}Uc=Oc}else Uc=!1;o_=Uc&&(!document.documentMode||9<document.documentMode)}function np(){Co&&(Co.detachEvent("onpropertychange",a_),Vo=Co=null)}function a_(t){if(t.propertyName==="value"&&ac(Vo)){var e=[];s_(e,Vo,t,Uh(t)),zg(Ux,e)}}function Fx(t,e,n){t==="focusin"?(np(),Co=e,Vo=n,Co.attachEvent("onpropertychange",a_)):t==="focusout"&&np()}function kx(t){if(t==="selectionchange"||t==="keyup"||t==="keydown")return ac(Vo)}function Bx(t,e){if(t==="click")return ac(e)}function zx(t,e){if(t==="input"||t==="change")return ac(e)}function Hx(t,e){return t===e&&(t!==0||1/t===1/e)||t!==t&&e!==e}var ii=typeof Object.is=="function"?Object.is:Hx;function Go(t,e){if(ii(t,e))return!0;if(typeof t!="object"||t===null||typeof e!="object"||e===null)return!1;var n=Object.keys(t),i=Object.keys(e);if(n.length!==i.length)return!1;for(i=0;i<n.length;i++){var r=n[i];if(!ju.call(e,r)||!ii(t[r],e[r]))return!1}return!0}function ip(t){for(;t&&t.firstChild;)t=t.firstChild;return t}function rp(t,e){var n=ip(t);t=0;for(var i;n;){if(n.nodeType===3){if(i=t+n.textContent.length,t<=e&&i>=e)return{node:n,offset:e-t};t=i}e:{for(;n;){if(n.nextSibling){n=n.nextSibling;break e}n=n.parentNode}n=void 0}n=ip(n)}}function l_(t,e){return t&&e?t===e?!0:t&&t.nodeType===3?!1:e&&e.nodeType===3?l_(t,e.parentNode):"contains"in t?t.contains(e):t.compareDocumentPosition?!!(t.compareDocumentPosition(e)&16):!1:!1}function c_(){for(var t=window,e=Al();e instanceof t.HTMLIFrameElement;){try{var n=typeof e.contentWindow.location.href=="string"}catch{n=!1}if(n)t=e.contentWindow;else break;e=Al(t.document)}return e}function jh(t){var e=t&&t.nodeName&&t.nodeName.toLowerCase();return e&&(e==="input"&&(t.type==="text"||t.type==="search"||t.type==="tel"||t.type==="url"||t.type==="password")||e==="textarea"||t.contentEditable==="true")}function Vx(t){var e=c_(),n=t.focusedElem,i=t.selectionRange;if(e!==n&&n&&n.ownerDocument&&l_(n.ownerDocument.documentElement,n)){if(i!==null&&jh(n)){if(e=i.start,t=i.end,t===void 0&&(t=e),"selectionStart"in n)n.selectionStart=e,n.selectionEnd=Math.min(t,n.value.length);else if(t=(e=n.ownerDocument||document)&&e.defaultView||window,t.getSelection){t=t.getSelection();var r=n.textContent.length,s=Math.min(i.start,r);i=i.end===void 0?s:Math.min(i.end,r),!t.extend&&s>i&&(r=i,i=s,s=r),r=rp(n,s);var o=rp(n,i);r&&o&&(t.rangeCount!==1||t.anchorNode!==r.node||t.anchorOffset!==r.offset||t.focusNode!==o.node||t.focusOffset!==o.offset)&&(e=e.createRange(),e.setStart(r.node,r.offset),t.removeAllRanges(),s>i?(t.addRange(e),t.extend(o.node,o.offset)):(e.setEnd(o.node,o.offset),t.addRange(e)))}}for(e=[],t=n;t=t.parentNode;)t.nodeType===1&&e.push({element:t,left:t.scrollLeft,top:t.scrollTop});for(typeof n.focus=="function"&&n.focus(),n=0;n<e.length;n++)t=e[n],t.element.scrollLeft=t.left,t.element.scrollTop=t.top}}var Gx=Li&&"documentMode"in document&&11>=document.documentMode,gs=null,cd=null,bo=null,ud=!1;function sp(t,e,n){var i=n.window===n?n.document:n.nodeType===9?n:n.ownerDocument;ud||gs==null||gs!==Al(i)||(i=gs,"selectionStart"in i&&jh(i)?i={start:i.selectionStart,end:i.selectionEnd}:(i=(i.ownerDocument&&i.ownerDocument.defaultView||window).getSelection(),i={anchorNode:i.anchorNode,anchorOffset:i.anchorOffset,focusNode:i.focusNode,focusOffset:i.focusOffset}),bo&&Go(bo,i)||(bo=i,i=Dl(cd,"onSelect"),0<i.length&&(e=new Hh("onSelect","select",null,e,n),t.push({event:e,listeners:i}),e.target=gs)))}function Ma(t,e){var n={};return n[t.toLowerCase()]=e.toLowerCase(),n["Webkit"+t]="webkit"+e,n["Moz"+t]="moz"+e,n}var _s={animationend:Ma("Animation","AnimationEnd"),animationiteration:Ma("Animation","AnimationIteration"),animationstart:Ma("Animation","AnimationStart"),transitionend:Ma("Transition","TransitionEnd")},Fc={},u_={};Li&&(u_=document.createElement("div").style,"AnimationEvent"in window||(delete _s.animationend.animation,delete _s.animationiteration.animation,delete _s.animationstart.animation),"TransitionEvent"in window||delete _s.transitionend.transition);function lc(t){if(Fc[t])return Fc[t];if(!_s[t])return t;var e=_s[t],n;for(n in e)if(e.hasOwnProperty(n)&&n in u_)return Fc[t]=e[n];return t}var d_=lc("animationend"),h_=lc("animationiteration"),f_=lc("animationstart"),p_=lc("transitionend"),m_=new Map,op="abort auxClick cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");function pr(t,e){m_.set(t,e),Wr(e,[t])}for(var kc=0;kc<op.length;kc++){var Bc=op[kc],jx=Bc.toLowerCase(),Wx=Bc[0].toUpperCase()+Bc.slice(1);pr(jx,"on"+Wx)}pr(d_,"onAnimationEnd");pr(h_,"onAnimationIteration");pr(f_,"onAnimationStart");pr("dblclick","onDoubleClick");pr("focusin","onFocus");pr("focusout","onBlur");pr(p_,"onTransitionEnd");Fs("onMouseEnter",["mouseout","mouseover"]);Fs("onMouseLeave",["mouseout","mouseover"]);Fs("onPointerEnter",["pointerout","pointerover"]);Fs("onPointerLeave",["pointerout","pointerover"]);Wr("onChange","change click focusin focusout input keydown keyup selectionchange".split(" "));Wr("onSelect","focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" "));Wr("onBeforeInput",["compositionend","keypress","textInput","paste"]);Wr("onCompositionEnd","compositionend focusout keydown keypress keyup mousedown".split(" "));Wr("onCompositionStart","compositionstart focusout keydown keypress keyup mousedown".split(" "));Wr("onCompositionUpdate","compositionupdate focusout keydown keypress keyup mousedown".split(" "));var So="abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(" "),Xx=new Set("cancel close invalid load scroll toggle".split(" ").concat(So));function ap(t,e,n){var i=t.type||"unknown-event";t.currentTarget=n,j0(i,e,void 0,t),t.currentTarget=null}function g_(t,e){e=(e&4)!==0;for(var n=0;n<t.length;n++){var i=t[n],r=i.event;i=i.listeners;e:{var s=void 0;if(e)for(var o=i.length-1;0<=o;o--){var a=i[o],l=a.instance,c=a.currentTarget;if(a=a.listener,l!==s&&r.isPropagationStopped())break e;ap(r,a,c),s=l}else for(o=0;o<i.length;o++){if(a=i[o],l=a.instance,c=a.currentTarget,a=a.listener,l!==s&&r.isPropagationStopped())break e;ap(r,a,c),s=l}}}if(bl)throw t=sd,bl=!1,sd=null,t}function _t(t,e){var n=e[md];n===void 0&&(n=e[md]=new Set);var i=t+"__bubble";n.has(i)||(__(e,t,2,!1),n.add(i))}function zc(t,e,n){var i=0;e&&(i|=4),__(n,t,i,e)}var Ea="_reactListening"+Math.random().toString(36).slice(2);function jo(t){if(!t[Ea]){t[Ea]=!0,wg.forEach(function(n){n!=="selectionchange"&&(Xx.has(n)||zc(n,!1,t),zc(n,!0,t))});var e=t.nodeType===9?t:t.ownerDocument;e===null||e[Ea]||(e[Ea]=!0,zc("selectionchange",!1,e))}}function __(t,e,n,i){switch(e_(e)){case 1:var r=ox;break;case 4:r=ax;break;default:r=Bh}n=r.bind(null,e,n,t),r=void 0,!rd||e!=="touchstart"&&e!=="touchmove"&&e!=="wheel"||(r=!0),i?r!==void 0?t.addEventListener(e,n,{capture:!0,passive:r}):t.addEventListener(e,n,!0):r!==void 0?t.addEventListener(e,n,{passive:r}):t.addEventListener(e,n,!1)}function Hc(t,e,n,i,r){var s=i;if(!(e&1)&&!(e&2)&&i!==null)e:for(;;){if(i===null)return;var o=i.tag;if(o===3||o===4){var a=i.stateNode.containerInfo;if(a===r||a.nodeType===8&&a.parentNode===r)break;if(o===4)for(o=i.return;o!==null;){var l=o.tag;if((l===3||l===4)&&(l=o.stateNode.containerInfo,l===r||l.nodeType===8&&l.parentNode===r))return;o=o.return}for(;a!==null;){if(o=Pr(a),o===null)return;if(l=o.tag,l===5||l===6){i=s=o;continue e}a=a.parentNode}}i=i.return}zg(function(){var c=s,d=Uh(n),h=[];e:{var f=m_.get(t);if(f!==void 0){var p=Hh,g=t;switch(t){case"keypress":if(ll(n)===0)break e;case"keydown":case"keyup":p=Mx;break;case"focusin":g="focus",p=Ic;break;case"focusout":g="blur",p=Ic;break;case"beforeblur":case"afterblur":p=Ic;break;case"click":if(n.button===2)break e;case"auxclick":case"dblclick":case"mousedown":case"mousemove":case"mouseup":case"mouseout":case"mouseover":case"contextmenu":p=qf;break;case"drag":case"dragend":case"dragenter":case"dragexit":case"dragleave":case"dragover":case"dragstart":case"drop":p=ux;break;case"touchcancel":case"touchend":case"touchmove":case"touchstart":p=Tx;break;case d_:case h_:case f_:p=fx;break;case p_:p=Cx;break;case"scroll":p=lx;break;case"wheel":p=Rx;break;case"copy":case"cut":case"paste":p=mx;break;case"gotpointercapture":case"lostpointercapture":case"pointercancel":case"pointerdown":case"pointermove":case"pointerout":case"pointerover":case"pointerup":p=Zf}var x=(e&4)!==0,m=!x&&t==="scroll",u=x?f!==null?f+"Capture":null:f;x=[];for(var _=c,v;_!==null;){v=_;var M=v.stateNode;if(v.tag===5&&M!==null&&(v=M,u!==null&&(M=ko(_,u),M!=null&&x.push(Wo(_,M,v)))),m)break;_=_.return}0<x.length&&(f=new p(f,g,null,n,d),h.push({event:f,listeners:x}))}}if(!(e&7)){e:{if(f=t==="mouseover"||t==="pointerover",p=t==="mouseout"||t==="pointerout",f&&n!==nd&&(g=n.relatedTarget||n.fromElement)&&(Pr(g)||g[Ni]))break e;if((p||f)&&(f=d.window===d?d:(f=d.ownerDocument)?f.defaultView||f.parentWindow:window,p?(g=n.relatedTarget||n.toElement,p=c,g=g?Pr(g):null,g!==null&&(m=Xr(g),g!==m||g.tag!==5&&g.tag!==6)&&(g=null)):(p=null,g=c),p!==g)){if(x=qf,M="onMouseLeave",u="onMouseEnter",_="mouse",(t==="pointerout"||t==="pointerover")&&(x=Zf,M="onPointerLeave",u="onPointerEnter",_="pointer"),m=p==null?f:vs(p),v=g==null?f:vs(g),f=new x(M,_+"leave",p,n,d),f.target=m,f.relatedTarget=v,M=null,Pr(d)===c&&(x=new x(u,_+"enter",g,n,d),x.target=v,x.relatedTarget=m,M=x),m=M,p&&g)t:{for(x=p,u=g,_=0,v=x;v;v=Kr(v))_++;for(v=0,M=u;M;M=Kr(M))v++;for(;0<_-v;)x=Kr(x),_--;for(;0<v-_;)u=Kr(u),v--;for(;_--;){if(x===u||u!==null&&x===u.alternate)break t;x=Kr(x),u=Kr(u)}x=null}else x=null;p!==null&&lp(h,f,p,x,!1),g!==null&&m!==null&&lp(h,m,g,x,!0)}}e:{if(f=c?vs(c):window,p=f.nodeName&&f.nodeName.toLowerCase(),p==="select"||p==="input"&&f.type==="file")var R=Ox;else if(ep(f))if(o_)R=zx;else{R=kx;var C=Fx}else(p=f.nodeName)&&p.toLowerCase()==="input"&&(f.type==="checkbox"||f.type==="radio")&&(R=Bx);if(R&&(R=R(t,c))){s_(h,R,n,d);break e}C&&C(t,f,c),t==="focusout"&&(C=f._wrapperState)&&C.controlled&&f.type==="number"&&Zu(f,"number",f.value)}switch(C=c?vs(c):window,t){case"focusin":(ep(C)||C.contentEditable==="true")&&(gs=C,cd=c,bo=null);break;case"focusout":bo=cd=gs=null;break;case"mousedown":ud=!0;break;case"contextmenu":case"mouseup":case"dragend":ud=!1,sp(h,n,d);break;case"selectionchange":if(Gx)break;case"keydown":case"keyup":sp(h,n,d)}var A;if(Gh)e:{switch(t){case"compositionstart":var P="onCompositionStart";break e;case"compositionend":P="onCompositionEnd";break e;case"compositionupdate":P="onCompositionUpdate";break e}P=void 0}else ms?i_(t,n)&&(P="onCompositionEnd"):t==="keydown"&&n.keyCode===229&&(P="onCompositionStart");P&&(n_&&n.locale!=="ko"&&(ms||P!=="onCompositionStart"?P==="onCompositionEnd"&&ms&&(A=t_()):(Ji=d,zh="value"in Ji?Ji.value:Ji.textContent,ms=!0)),C=Dl(c,P),0<C.length&&(P=new Kf(P,t,null,n,d),h.push({event:P,listeners:C}),A?P.data=A:(A=r_(n),A!==null&&(P.data=A)))),(A=Lx?Nx(t,n):Dx(t,n))&&(c=Dl(c,"onBeforeInput"),0<c.length&&(d=new Kf("onBeforeInput","beforeinput",null,n,d),h.push({event:d,listeners:c}),d.data=A))}g_(h,e)})}function Wo(t,e,n){return{instance:t,listener:e,currentTarget:n}}function Dl(t,e){for(var n=e+"Capture",i=[];t!==null;){var r=t,s=r.stateNode;r.tag===5&&s!==null&&(r=s,s=ko(t,n),s!=null&&i.unshift(Wo(t,s,r)),s=ko(t,e),s!=null&&i.push(Wo(t,s,r))),t=t.return}return i}function Kr(t){if(t===null)return null;do t=t.return;while(t&&t.tag!==5);return t||null}function lp(t,e,n,i,r){for(var s=e._reactName,o=[];n!==null&&n!==i;){var a=n,l=a.alternate,c=a.stateNode;if(l!==null&&l===i)break;a.tag===5&&c!==null&&(a=c,r?(l=ko(n,s),l!=null&&o.unshift(Wo(n,l,a))):r||(l=ko(n,s),l!=null&&o.push(Wo(n,l,a)))),n=n.return}o.length!==0&&t.push({event:e,listeners:o})}var $x=/\r\n?/g,Yx=/\u0000|\uFFFD/g;function cp(t){return(typeof t=="string"?t:""+t).replace($x,`
`).replace(Yx,"")}function wa(t,e,n){if(e=cp(e),cp(t)!==e&&n)throw Error(he(425))}function Il(){}var dd=null,hd=null;function fd(t,e){return t==="textarea"||t==="noscript"||typeof e.children=="string"||typeof e.children=="number"||typeof e.dangerouslySetInnerHTML=="object"&&e.dangerouslySetInnerHTML!==null&&e.dangerouslySetInnerHTML.__html!=null}var pd=typeof setTimeout=="function"?setTimeout:void 0,qx=typeof clearTimeout=="function"?clearTimeout:void 0,up=typeof Promise=="function"?Promise:void 0,Kx=typeof queueMicrotask=="function"?queueMicrotask:typeof up<"u"?function(t){return up.resolve(null).then(t).catch(Zx)}:pd;function Zx(t){setTimeout(function(){throw t})}function Vc(t,e){var n=e,i=0;do{var r=n.nextSibling;if(t.removeChild(n),r&&r.nodeType===8)if(n=r.data,n==="/$"){if(i===0){t.removeChild(r),Ho(e);return}i--}else n!=="$"&&n!=="$?"&&n!=="$!"||i++;n=r}while(n);Ho(e)}function ir(t){for(;t!=null;t=t.nextSibling){var e=t.nodeType;if(e===1||e===3)break;if(e===8){if(e=t.data,e==="$"||e==="$!"||e==="$?")break;if(e==="/$")return null}}return t}function dp(t){t=t.previousSibling;for(var e=0;t;){if(t.nodeType===8){var n=t.data;if(n==="$"||n==="$!"||n==="$?"){if(e===0)return t;e--}else n==="/$"&&e++}t=t.previousSibling}return null}var Qs=Math.random().toString(36).slice(2),ai="__reactFiber$"+Qs,Xo="__reactProps$"+Qs,Ni="__reactContainer$"+Qs,md="__reactEvents$"+Qs,Jx="__reactListeners$"+Qs,Qx="__reactHandles$"+Qs;function Pr(t){var e=t[ai];if(e)return e;for(var n=t.parentNode;n;){if(e=n[Ni]||n[ai]){if(n=e.alternate,e.child!==null||n!==null&&n.child!==null)for(t=dp(t);t!==null;){if(n=t[ai])return n;t=dp(t)}return e}t=n,n=t.parentNode}return null}function ra(t){return t=t[ai]||t[Ni],!t||t.tag!==5&&t.tag!==6&&t.tag!==13&&t.tag!==3?null:t}function vs(t){if(t.tag===5||t.tag===6)return t.stateNode;throw Error(he(33))}function cc(t){return t[Xo]||null}var gd=[],xs=-1;function mr(t){return{current:t}}function vt(t){0>xs||(t.current=gd[xs],gd[xs]=null,xs--)}function gt(t,e){xs++,gd[xs]=t.current,t.current=e}var dr={},en=mr(dr),fn=mr(!1),Fr=dr;function ks(t,e){var n=t.type.contextTypes;if(!n)return dr;var i=t.stateNode;if(i&&i.__reactInternalMemoizedUnmaskedChildContext===e)return i.__reactInternalMemoizedMaskedChildContext;var r={},s;for(s in n)r[s]=e[s];return i&&(t=t.stateNode,t.__reactInternalMemoizedUnmaskedChildContext=e,t.__reactInternalMemoizedMaskedChildContext=r),r}function pn(t){return t=t.childContextTypes,t!=null}function Ul(){vt(fn),vt(en)}function hp(t,e,n){if(en.current!==dr)throw Error(he(168));gt(en,e),gt(fn,n)}function v_(t,e,n){var i=t.stateNode;if(e=e.childContextTypes,typeof i.getChildContext!="function")return n;i=i.getChildContext();for(var r in i)if(!(r in e))throw Error(he(108,F0(t)||"Unknown",r));return Tt({},n,i)}function Ol(t){return t=(t=t.stateNode)&&t.__reactInternalMemoizedMergedChildContext||dr,Fr=en.current,gt(en,t),gt(fn,fn.current),!0}function fp(t,e,n){var i=t.stateNode;if(!i)throw Error(he(169));n?(t=v_(t,e,Fr),i.__reactInternalMemoizedMergedChildContext=t,vt(fn),vt(en),gt(en,t)):vt(fn),gt(fn,n)}var Ei=null,uc=!1,Gc=!1;function x_(t){Ei===null?Ei=[t]:Ei.push(t)}function ey(t){uc=!0,x_(t)}function gr(){if(!Gc&&Ei!==null){Gc=!0;var t=0,e=ht;try{var n=Ei;for(ht=1;t<n.length;t++){var i=n[t];do i=i(!0);while(i!==null)}Ei=null,uc=!1}catch(r){throw Ei!==null&&(Ei=Ei.slice(t+1)),jg(Oh,gr),r}finally{ht=e,Gc=!1}}return null}var ys=[],Ss=0,Fl=null,kl=0,Un=[],On=0,kr=null,Ti=1,Ai="";function Tr(t,e){ys[Ss++]=kl,ys[Ss++]=Fl,Fl=t,kl=e}function y_(t,e,n){Un[On++]=Ti,Un[On++]=Ai,Un[On++]=kr,kr=t;var i=Ti;t=Ai;var r=32-ei(i)-1;i&=~(1<<r),n+=1;var s=32-ei(e)+r;if(30<s){var o=r-r%5;s=(i&(1<<o)-1).toString(32),i>>=o,r-=o,Ti=1<<32-ei(e)+r|n<<r|i,Ai=s+t}else Ti=1<<s|n<<r|i,Ai=t}function Wh(t){t.return!==null&&(Tr(t,1),y_(t,1,0))}function Xh(t){for(;t===Fl;)Fl=ys[--Ss],ys[Ss]=null,kl=ys[--Ss],ys[Ss]=null;for(;t===kr;)kr=Un[--On],Un[On]=null,Ai=Un[--On],Un[On]=null,Ti=Un[--On],Un[On]=null}var An=null,wn=null,Mt=!1,Zn=null;function S_(t,e){var n=kn(5,null,null,0);n.elementType="DELETED",n.stateNode=e,n.return=t,e=t.deletions,e===null?(t.deletions=[n],t.flags|=16):e.push(n)}function pp(t,e){switch(t.tag){case 5:var n=t.type;return e=e.nodeType!==1||n.toLowerCase()!==e.nodeName.toLowerCase()?null:e,e!==null?(t.stateNode=e,An=t,wn=ir(e.firstChild),!0):!1;case 6:return e=t.pendingProps===""||e.nodeType!==3?null:e,e!==null?(t.stateNode=e,An=t,wn=null,!0):!1;case 13:return e=e.nodeType!==8?null:e,e!==null?(n=kr!==null?{id:Ti,overflow:Ai}:null,t.memoizedState={dehydrated:e,treeContext:n,retryLane:1073741824},n=kn(18,null,null,0),n.stateNode=e,n.return=t,t.child=n,An=t,wn=null,!0):!1;default:return!1}}function _d(t){return(t.mode&1)!==0&&(t.flags&128)===0}function vd(t){if(Mt){var e=wn;if(e){var n=e;if(!pp(t,e)){if(_d(t))throw Error(he(418));e=ir(n.nextSibling);var i=An;e&&pp(t,e)?S_(i,n):(t.flags=t.flags&-4097|2,Mt=!1,An=t)}}else{if(_d(t))throw Error(he(418));t.flags=t.flags&-4097|2,Mt=!1,An=t}}}function mp(t){for(t=t.return;t!==null&&t.tag!==5&&t.tag!==3&&t.tag!==13;)t=t.return;An=t}function Ta(t){if(t!==An)return!1;if(!Mt)return mp(t),Mt=!0,!1;var e;if((e=t.tag!==3)&&!(e=t.tag!==5)&&(e=t.type,e=e!=="head"&&e!=="body"&&!fd(t.type,t.memoizedProps)),e&&(e=wn)){if(_d(t))throw M_(),Error(he(418));for(;e;)S_(t,e),e=ir(e.nextSibling)}if(mp(t),t.tag===13){if(t=t.memoizedState,t=t!==null?t.dehydrated:null,!t)throw Error(he(317));e:{for(t=t.nextSibling,e=0;t;){if(t.nodeType===8){var n=t.data;if(n==="/$"){if(e===0){wn=ir(t.nextSibling);break e}e--}else n!=="$"&&n!=="$!"&&n!=="$?"||e++}t=t.nextSibling}wn=null}}else wn=An?ir(t.stateNode.nextSibling):null;return!0}function M_(){for(var t=wn;t;)t=ir(t.nextSibling)}function Bs(){wn=An=null,Mt=!1}function $h(t){Zn===null?Zn=[t]:Zn.push(t)}var ty=Oi.ReactCurrentBatchConfig;function lo(t,e,n){if(t=n.ref,t!==null&&typeof t!="function"&&typeof t!="object"){if(n._owner){if(n=n._owner,n){if(n.tag!==1)throw Error(he(309));var i=n.stateNode}if(!i)throw Error(he(147,t));var r=i,s=""+t;return e!==null&&e.ref!==null&&typeof e.ref=="function"&&e.ref._stringRef===s?e.ref:(e=function(o){var a=r.refs;o===null?delete a[s]:a[s]=o},e._stringRef=s,e)}if(typeof t!="string")throw Error(he(284));if(!n._owner)throw Error(he(290,t))}return t}function Aa(t,e){throw t=Object.prototype.toString.call(e),Error(he(31,t==="[object Object]"?"object with keys {"+Object.keys(e).join(", ")+"}":t))}function gp(t){var e=t._init;return e(t._payload)}function E_(t){function e(u,_){if(t){var v=u.deletions;v===null?(u.deletions=[_],u.flags|=16):v.push(_)}}function n(u,_){if(!t)return null;for(;_!==null;)e(u,_),_=_.sibling;return null}function i(u,_){for(u=new Map;_!==null;)_.key!==null?u.set(_.key,_):u.set(_.index,_),_=_.sibling;return u}function r(u,_){return u=ar(u,_),u.index=0,u.sibling=null,u}function s(u,_,v){return u.index=v,t?(v=u.alternate,v!==null?(v=v.index,v<_?(u.flags|=2,_):v):(u.flags|=2,_)):(u.flags|=1048576,_)}function o(u){return t&&u.alternate===null&&(u.flags|=2),u}function a(u,_,v,M){return _===null||_.tag!==6?(_=Kc(v,u.mode,M),_.return=u,_):(_=r(_,v),_.return=u,_)}function l(u,_,v,M){var R=v.type;return R===ps?d(u,_,v.props.children,M,v.key):_!==null&&(_.elementType===R||typeof R=="object"&&R!==null&&R.$$typeof===Xi&&gp(R)===_.type)?(M=r(_,v.props),M.ref=lo(u,_,v),M.return=u,M):(M=ml(v.type,v.key,v.props,null,u.mode,M),M.ref=lo(u,_,v),M.return=u,M)}function c(u,_,v,M){return _===null||_.tag!==4||_.stateNode.containerInfo!==v.containerInfo||_.stateNode.implementation!==v.implementation?(_=Zc(v,u.mode,M),_.return=u,_):(_=r(_,v.children||[]),_.return=u,_)}function d(u,_,v,M,R){return _===null||_.tag!==7?(_=Or(v,u.mode,M,R),_.return=u,_):(_=r(_,v),_.return=u,_)}function h(u,_,v){if(typeof _=="string"&&_!==""||typeof _=="number")return _=Kc(""+_,u.mode,v),_.return=u,_;if(typeof _=="object"&&_!==null){switch(_.$$typeof){case ma:return v=ml(_.type,_.key,_.props,null,u.mode,v),v.ref=lo(u,null,_),v.return=u,v;case fs:return _=Zc(_,u.mode,v),_.return=u,_;case Xi:var M=_._init;return h(u,M(_._payload),v)}if(xo(_)||io(_))return _=Or(_,u.mode,v,null),_.return=u,_;Aa(u,_)}return null}function f(u,_,v,M){var R=_!==null?_.key:null;if(typeof v=="string"&&v!==""||typeof v=="number")return R!==null?null:a(u,_,""+v,M);if(typeof v=="object"&&v!==null){switch(v.$$typeof){case ma:return v.key===R?l(u,_,v,M):null;case fs:return v.key===R?c(u,_,v,M):null;case Xi:return R=v._init,f(u,_,R(v._payload),M)}if(xo(v)||io(v))return R!==null?null:d(u,_,v,M,null);Aa(u,v)}return null}function p(u,_,v,M,R){if(typeof M=="string"&&M!==""||typeof M=="number")return u=u.get(v)||null,a(_,u,""+M,R);if(typeof M=="object"&&M!==null){switch(M.$$typeof){case ma:return u=u.get(M.key===null?v:M.key)||null,l(_,u,M,R);case fs:return u=u.get(M.key===null?v:M.key)||null,c(_,u,M,R);case Xi:var C=M._init;return p(u,_,v,C(M._payload),R)}if(xo(M)||io(M))return u=u.get(v)||null,d(_,u,M,R,null);Aa(_,M)}return null}function g(u,_,v,M){for(var R=null,C=null,A=_,P=_=0,E=null;A!==null&&P<v.length;P++){A.index>P?(E=A,A=null):E=A.sibling;var S=f(u,A,v[P],M);if(S===null){A===null&&(A=E);break}t&&A&&S.alternate===null&&e(u,A),_=s(S,_,P),C===null?R=S:C.sibling=S,C=S,A=E}if(P===v.length)return n(u,A),Mt&&Tr(u,P),R;if(A===null){for(;P<v.length;P++)A=h(u,v[P],M),A!==null&&(_=s(A,_,P),C===null?R=A:C.sibling=A,C=A);return Mt&&Tr(u,P),R}for(A=i(u,A);P<v.length;P++)E=p(A,u,P,v[P],M),E!==null&&(t&&E.alternate!==null&&A.delete(E.key===null?P:E.key),_=s(E,_,P),C===null?R=E:C.sibling=E,C=E);return t&&A.forEach(function(D){return e(u,D)}),Mt&&Tr(u,P),R}function x(u,_,v,M){var R=io(v);if(typeof R!="function")throw Error(he(150));if(v=R.call(v),v==null)throw Error(he(151));for(var C=R=null,A=_,P=_=0,E=null,S=v.next();A!==null&&!S.done;P++,S=v.next()){A.index>P?(E=A,A=null):E=A.sibling;var D=f(u,A,S.value,M);if(D===null){A===null&&(A=E);break}t&&A&&D.alternate===null&&e(u,A),_=s(D,_,P),C===null?R=D:C.sibling=D,C=D,A=E}if(S.done)return n(u,A),Mt&&Tr(u,P),R;if(A===null){for(;!S.done;P++,S=v.next())S=h(u,S.value,M),S!==null&&(_=s(S,_,P),C===null?R=S:C.sibling=S,C=S);return Mt&&Tr(u,P),R}for(A=i(u,A);!S.done;P++,S=v.next())S=p(A,u,P,S.value,M),S!==null&&(t&&S.alternate!==null&&A.delete(S.key===null?P:S.key),_=s(S,_,P),C===null?R=S:C.sibling=S,C=S);return t&&A.forEach(function(X){return e(u,X)}),Mt&&Tr(u,P),R}function m(u,_,v,M){if(typeof v=="object"&&v!==null&&v.type===ps&&v.key===null&&(v=v.props.children),typeof v=="object"&&v!==null){switch(v.$$typeof){case ma:e:{for(var R=v.key,C=_;C!==null;){if(C.key===R){if(R=v.type,R===ps){if(C.tag===7){n(u,C.sibling),_=r(C,v.props.children),_.return=u,u=_;break e}}else if(C.elementType===R||typeof R=="object"&&R!==null&&R.$$typeof===Xi&&gp(R)===C.type){n(u,C.sibling),_=r(C,v.props),_.ref=lo(u,C,v),_.return=u,u=_;break e}n(u,C);break}else e(u,C);C=C.sibling}v.type===ps?(_=Or(v.props.children,u.mode,M,v.key),_.return=u,u=_):(M=ml(v.type,v.key,v.props,null,u.mode,M),M.ref=lo(u,_,v),M.return=u,u=M)}return o(u);case fs:e:{for(C=v.key;_!==null;){if(_.key===C)if(_.tag===4&&_.stateNode.containerInfo===v.containerInfo&&_.stateNode.implementation===v.implementation){n(u,_.sibling),_=r(_,v.children||[]),_.return=u,u=_;break e}else{n(u,_);break}else e(u,_);_=_.sibling}_=Zc(v,u.mode,M),_.return=u,u=_}return o(u);case Xi:return C=v._init,m(u,_,C(v._payload),M)}if(xo(v))return g(u,_,v,M);if(io(v))return x(u,_,v,M);Aa(u,v)}return typeof v=="string"&&v!==""||typeof v=="number"?(v=""+v,_!==null&&_.tag===6?(n(u,_.sibling),_=r(_,v),_.return=u,u=_):(n(u,_),_=Kc(v,u.mode,M),_.return=u,u=_),o(u)):n(u,_)}return m}var zs=E_(!0),w_=E_(!1),Bl=mr(null),zl=null,Ms=null,Yh=null;function qh(){Yh=Ms=zl=null}function Kh(t){var e=Bl.current;vt(Bl),t._currentValue=e}function xd(t,e,n){for(;t!==null;){var i=t.alternate;if((t.childLanes&e)!==e?(t.childLanes|=e,i!==null&&(i.childLanes|=e)):i!==null&&(i.childLanes&e)!==e&&(i.childLanes|=e),t===n)break;t=t.return}}function Ls(t,e){zl=t,Yh=Ms=null,t=t.dependencies,t!==null&&t.firstContext!==null&&(t.lanes&e&&(hn=!0),t.firstContext=null)}function zn(t){var e=t._currentValue;if(Yh!==t)if(t={context:t,memoizedValue:e,next:null},Ms===null){if(zl===null)throw Error(he(308));Ms=t,zl.dependencies={lanes:0,firstContext:t}}else Ms=Ms.next=t;return e}var Lr=null;function Zh(t){Lr===null?Lr=[t]:Lr.push(t)}function T_(t,e,n,i){var r=e.interleaved;return r===null?(n.next=n,Zh(e)):(n.next=r.next,r.next=n),e.interleaved=n,Di(t,i)}function Di(t,e){t.lanes|=e;var n=t.alternate;for(n!==null&&(n.lanes|=e),n=t,t=t.return;t!==null;)t.childLanes|=e,n=t.alternate,n!==null&&(n.childLanes|=e),n=t,t=t.return;return n.tag===3?n.stateNode:null}var $i=!1;function Jh(t){t.updateQueue={baseState:t.memoizedState,firstBaseUpdate:null,lastBaseUpdate:null,shared:{pending:null,interleaved:null,lanes:0},effects:null}}function A_(t,e){t=t.updateQueue,e.updateQueue===t&&(e.updateQueue={baseState:t.baseState,firstBaseUpdate:t.firstBaseUpdate,lastBaseUpdate:t.lastBaseUpdate,shared:t.shared,effects:t.effects})}function Ri(t,e){return{eventTime:t,lane:e,tag:0,payload:null,callback:null,next:null}}function rr(t,e,n){var i=t.updateQueue;if(i===null)return null;if(i=i.shared,ot&2){var r=i.pending;return r===null?e.next=e:(e.next=r.next,r.next=e),i.pending=e,Di(t,n)}return r=i.interleaved,r===null?(e.next=e,Zh(i)):(e.next=r.next,r.next=e),i.interleaved=e,Di(t,n)}function cl(t,e,n){if(e=e.updateQueue,e!==null&&(e=e.shared,(n&4194240)!==0)){var i=e.lanes;i&=t.pendingLanes,n|=i,e.lanes=n,Fh(t,n)}}function _p(t,e){var n=t.updateQueue,i=t.alternate;if(i!==null&&(i=i.updateQueue,n===i)){var r=null,s=null;if(n=n.firstBaseUpdate,n!==null){do{var o={eventTime:n.eventTime,lane:n.lane,tag:n.tag,payload:n.payload,callback:n.callback,next:null};s===null?r=s=o:s=s.next=o,n=n.next}while(n!==null);s===null?r=s=e:s=s.next=e}else r=s=e;n={baseState:i.baseState,firstBaseUpdate:r,lastBaseUpdate:s,shared:i.shared,effects:i.effects},t.updateQueue=n;return}t=n.lastBaseUpdate,t===null?n.firstBaseUpdate=e:t.next=e,n.lastBaseUpdate=e}function Hl(t,e,n,i){var r=t.updateQueue;$i=!1;var s=r.firstBaseUpdate,o=r.lastBaseUpdate,a=r.shared.pending;if(a!==null){r.shared.pending=null;var l=a,c=l.next;l.next=null,o===null?s=c:o.next=c,o=l;var d=t.alternate;d!==null&&(d=d.updateQueue,a=d.lastBaseUpdate,a!==o&&(a===null?d.firstBaseUpdate=c:a.next=c,d.lastBaseUpdate=l))}if(s!==null){var h=r.baseState;o=0,d=c=l=null,a=s;do{var f=a.lane,p=a.eventTime;if((i&f)===f){d!==null&&(d=d.next={eventTime:p,lane:0,tag:a.tag,payload:a.payload,callback:a.callback,next:null});e:{var g=t,x=a;switch(f=e,p=n,x.tag){case 1:if(g=x.payload,typeof g=="function"){h=g.call(p,h,f);break e}h=g;break e;case 3:g.flags=g.flags&-65537|128;case 0:if(g=x.payload,f=typeof g=="function"?g.call(p,h,f):g,f==null)break e;h=Tt({},h,f);break e;case 2:$i=!0}}a.callback!==null&&a.lane!==0&&(t.flags|=64,f=r.effects,f===null?r.effects=[a]:f.push(a))}else p={eventTime:p,lane:f,tag:a.tag,payload:a.payload,callback:a.callback,next:null},d===null?(c=d=p,l=h):d=d.next=p,o|=f;if(a=a.next,a===null){if(a=r.shared.pending,a===null)break;f=a,a=f.next,f.next=null,r.lastBaseUpdate=f,r.shared.pending=null}}while(!0);if(d===null&&(l=h),r.baseState=l,r.firstBaseUpdate=c,r.lastBaseUpdate=d,e=r.shared.interleaved,e!==null){r=e;do o|=r.lane,r=r.next;while(r!==e)}else s===null&&(r.shared.lanes=0);zr|=o,t.lanes=o,t.memoizedState=h}}function vp(t,e,n){if(t=e.effects,e.effects=null,t!==null)for(e=0;e<t.length;e++){var i=t[e],r=i.callback;if(r!==null){if(i.callback=null,i=n,typeof r!="function")throw Error(he(191,r));r.call(i)}}}var sa={},ui=mr(sa),$o=mr(sa),Yo=mr(sa);function Nr(t){if(t===sa)throw Error(he(174));return t}function Qh(t,e){switch(gt(Yo,e),gt($o,t),gt(ui,sa),t=e.nodeType,t){case 9:case 11:e=(e=e.documentElement)?e.namespaceURI:Qu(null,"");break;default:t=t===8?e.parentNode:e,e=t.namespaceURI||null,t=t.tagName,e=Qu(e,t)}vt(ui),gt(ui,e)}function Hs(){vt(ui),vt($o),vt(Yo)}function C_(t){Nr(Yo.current);var e=Nr(ui.current),n=Qu(e,t.type);e!==n&&(gt($o,t),gt(ui,n))}function ef(t){$o.current===t&&(vt(ui),vt($o))}var Et=mr(0);function Vl(t){for(var e=t;e!==null;){if(e.tag===13){var n=e.memoizedState;if(n!==null&&(n=n.dehydrated,n===null||n.data==="$?"||n.data==="$!"))return e}else if(e.tag===19&&e.memoizedProps.revealOrder!==void 0){if(e.flags&128)return e}else if(e.child!==null){e.child.return=e,e=e.child;continue}if(e===t)break;for(;e.sibling===null;){if(e.return===null||e.return===t)return null;e=e.return}e.sibling.return=e.return,e=e.sibling}return null}var jc=[];function tf(){for(var t=0;t<jc.length;t++)jc[t]._workInProgressVersionPrimary=null;jc.length=0}var ul=Oi.ReactCurrentDispatcher,Wc=Oi.ReactCurrentBatchConfig,Br=0,wt=null,Ot=null,Vt=null,Gl=!1,Ro=!1,qo=0,ny=0;function qt(){throw Error(he(321))}function nf(t,e){if(e===null)return!1;for(var n=0;n<e.length&&n<t.length;n++)if(!ii(t[n],e[n]))return!1;return!0}function rf(t,e,n,i,r,s){if(Br=s,wt=e,e.memoizedState=null,e.updateQueue=null,e.lanes=0,ul.current=t===null||t.memoizedState===null?oy:ay,t=n(i,r),Ro){s=0;do{if(Ro=!1,qo=0,25<=s)throw Error(he(301));s+=1,Vt=Ot=null,e.updateQueue=null,ul.current=ly,t=n(i,r)}while(Ro)}if(ul.current=jl,e=Ot!==null&&Ot.next!==null,Br=0,Vt=Ot=wt=null,Gl=!1,e)throw Error(he(300));return t}function sf(){var t=qo!==0;return qo=0,t}function si(){var t={memoizedState:null,baseState:null,baseQueue:null,queue:null,next:null};return Vt===null?wt.memoizedState=Vt=t:Vt=Vt.next=t,Vt}function Hn(){if(Ot===null){var t=wt.alternate;t=t!==null?t.memoizedState:null}else t=Ot.next;var e=Vt===null?wt.memoizedState:Vt.next;if(e!==null)Vt=e,Ot=t;else{if(t===null)throw Error(he(310));Ot=t,t={memoizedState:Ot.memoizedState,baseState:Ot.baseState,baseQueue:Ot.baseQueue,queue:Ot.queue,next:null},Vt===null?wt.memoizedState=Vt=t:Vt=Vt.next=t}return Vt}function Ko(t,e){return typeof e=="function"?e(t):e}function Xc(t){var e=Hn(),n=e.queue;if(n===null)throw Error(he(311));n.lastRenderedReducer=t;var i=Ot,r=i.baseQueue,s=n.pending;if(s!==null){if(r!==null){var o=r.next;r.next=s.next,s.next=o}i.baseQueue=r=s,n.pending=null}if(r!==null){s=r.next,i=i.baseState;var a=o=null,l=null,c=s;do{var d=c.lane;if((Br&d)===d)l!==null&&(l=l.next={lane:0,action:c.action,hasEagerState:c.hasEagerState,eagerState:c.eagerState,next:null}),i=c.hasEagerState?c.eagerState:t(i,c.action);else{var h={lane:d,action:c.action,hasEagerState:c.hasEagerState,eagerState:c.eagerState,next:null};l===null?(a=l=h,o=i):l=l.next=h,wt.lanes|=d,zr|=d}c=c.next}while(c!==null&&c!==s);l===null?o=i:l.next=a,ii(i,e.memoizedState)||(hn=!0),e.memoizedState=i,e.baseState=o,e.baseQueue=l,n.lastRenderedState=i}if(t=n.interleaved,t!==null){r=t;do s=r.lane,wt.lanes|=s,zr|=s,r=r.next;while(r!==t)}else r===null&&(n.lanes=0);return[e.memoizedState,n.dispatch]}function $c(t){var e=Hn(),n=e.queue;if(n===null)throw Error(he(311));n.lastRenderedReducer=t;var i=n.dispatch,r=n.pending,s=e.memoizedState;if(r!==null){n.pending=null;var o=r=r.next;do s=t(s,o.action),o=o.next;while(o!==r);ii(s,e.memoizedState)||(hn=!0),e.memoizedState=s,e.baseQueue===null&&(e.baseState=s),n.lastRenderedState=s}return[s,i]}function b_(){}function R_(t,e){var n=wt,i=Hn(),r=e(),s=!ii(i.memoizedState,r);if(s&&(i.memoizedState=r,hn=!0),i=i.queue,of(N_.bind(null,n,i,t),[t]),i.getSnapshot!==e||s||Vt!==null&&Vt.memoizedState.tag&1){if(n.flags|=2048,Zo(9,L_.bind(null,n,i,r,e),void 0,null),Gt===null)throw Error(he(349));Br&30||P_(n,e,r)}return r}function P_(t,e,n){t.flags|=16384,t={getSnapshot:e,value:n},e=wt.updateQueue,e===null?(e={lastEffect:null,stores:null},wt.updateQueue=e,e.stores=[t]):(n=e.stores,n===null?e.stores=[t]:n.push(t))}function L_(t,e,n,i){e.value=n,e.getSnapshot=i,D_(e)&&I_(t)}function N_(t,e,n){return n(function(){D_(e)&&I_(t)})}function D_(t){var e=t.getSnapshot;t=t.value;try{var n=e();return!ii(t,n)}catch{return!0}}function I_(t){var e=Di(t,1);e!==null&&ti(e,t,1,-1)}function xp(t){var e=si();return typeof t=="function"&&(t=t()),e.memoizedState=e.baseState=t,t={pending:null,interleaved:null,lanes:0,dispatch:null,lastRenderedReducer:Ko,lastRenderedState:t},e.queue=t,t=t.dispatch=sy.bind(null,wt,t),[e.memoizedState,t]}function Zo(t,e,n,i){return t={tag:t,create:e,destroy:n,deps:i,next:null},e=wt.updateQueue,e===null?(e={lastEffect:null,stores:null},wt.updateQueue=e,e.lastEffect=t.next=t):(n=e.lastEffect,n===null?e.lastEffect=t.next=t:(i=n.next,n.next=t,t.next=i,e.lastEffect=t)),t}function U_(){return Hn().memoizedState}function dl(t,e,n,i){var r=si();wt.flags|=t,r.memoizedState=Zo(1|e,n,void 0,i===void 0?null:i)}function dc(t,e,n,i){var r=Hn();i=i===void 0?null:i;var s=void 0;if(Ot!==null){var o=Ot.memoizedState;if(s=o.destroy,i!==null&&nf(i,o.deps)){r.memoizedState=Zo(e,n,s,i);return}}wt.flags|=t,r.memoizedState=Zo(1|e,n,s,i)}function yp(t,e){return dl(8390656,8,t,e)}function of(t,e){return dc(2048,8,t,e)}function O_(t,e){return dc(4,2,t,e)}function F_(t,e){return dc(4,4,t,e)}function k_(t,e){if(typeof e=="function")return t=t(),e(t),function(){e(null)};if(e!=null)return t=t(),e.current=t,function(){e.current=null}}function B_(t,e,n){return n=n!=null?n.concat([t]):null,dc(4,4,k_.bind(null,e,t),n)}function af(){}function z_(t,e){var n=Hn();e=e===void 0?null:e;var i=n.memoizedState;return i!==null&&e!==null&&nf(e,i[1])?i[0]:(n.memoizedState=[t,e],t)}function H_(t,e){var n=Hn();e=e===void 0?null:e;var i=n.memoizedState;return i!==null&&e!==null&&nf(e,i[1])?i[0]:(t=t(),n.memoizedState=[t,e],t)}function V_(t,e,n){return Br&21?(ii(n,e)||(n=$g(),wt.lanes|=n,zr|=n,t.baseState=!0),e):(t.baseState&&(t.baseState=!1,hn=!0),t.memoizedState=n)}function iy(t,e){var n=ht;ht=n!==0&&4>n?n:4,t(!0);var i=Wc.transition;Wc.transition={};try{t(!1),e()}finally{ht=n,Wc.transition=i}}function G_(){return Hn().memoizedState}function ry(t,e,n){var i=or(t);if(n={lane:i,action:n,hasEagerState:!1,eagerState:null,next:null},j_(t))W_(e,n);else if(n=T_(t,e,n,i),n!==null){var r=sn();ti(n,t,i,r),X_(n,e,i)}}function sy(t,e,n){var i=or(t),r={lane:i,action:n,hasEagerState:!1,eagerState:null,next:null};if(j_(t))W_(e,r);else{var s=t.alternate;if(t.lanes===0&&(s===null||s.lanes===0)&&(s=e.lastRenderedReducer,s!==null))try{var o=e.lastRenderedState,a=s(o,n);if(r.hasEagerState=!0,r.eagerState=a,ii(a,o)){var l=e.interleaved;l===null?(r.next=r,Zh(e)):(r.next=l.next,l.next=r),e.interleaved=r;return}}catch{}finally{}n=T_(t,e,r,i),n!==null&&(r=sn(),ti(n,t,i,r),X_(n,e,i))}}function j_(t){var e=t.alternate;return t===wt||e!==null&&e===wt}function W_(t,e){Ro=Gl=!0;var n=t.pending;n===null?e.next=e:(e.next=n.next,n.next=e),t.pending=e}function X_(t,e,n){if(n&4194240){var i=e.lanes;i&=t.pendingLanes,n|=i,e.lanes=n,Fh(t,n)}}var jl={readContext:zn,useCallback:qt,useContext:qt,useEffect:qt,useImperativeHandle:qt,useInsertionEffect:qt,useLayoutEffect:qt,useMemo:qt,useReducer:qt,useRef:qt,useState:qt,useDebugValue:qt,useDeferredValue:qt,useTransition:qt,useMutableSource:qt,useSyncExternalStore:qt,useId:qt,unstable_isNewReconciler:!1},oy={readContext:zn,useCallback:function(t,e){return si().memoizedState=[t,e===void 0?null:e],t},useContext:zn,useEffect:yp,useImperativeHandle:function(t,e,n){return n=n!=null?n.concat([t]):null,dl(4194308,4,k_.bind(null,e,t),n)},useLayoutEffect:function(t,e){return dl(4194308,4,t,e)},useInsertionEffect:function(t,e){return dl(4,2,t,e)},useMemo:function(t,e){var n=si();return e=e===void 0?null:e,t=t(),n.memoizedState=[t,e],t},useReducer:function(t,e,n){var i=si();return e=n!==void 0?n(e):e,i.memoizedState=i.baseState=e,t={pending:null,interleaved:null,lanes:0,dispatch:null,lastRenderedReducer:t,lastRenderedState:e},i.queue=t,t=t.dispatch=ry.bind(null,wt,t),[i.memoizedState,t]},useRef:function(t){var e=si();return t={current:t},e.memoizedState=t},useState:xp,useDebugValue:af,useDeferredValue:function(t){return si().memoizedState=t},useTransition:function(){var t=xp(!1),e=t[0];return t=iy.bind(null,t[1]),si().memoizedState=t,[e,t]},useMutableSource:function(){},useSyncExternalStore:function(t,e,n){var i=wt,r=si();if(Mt){if(n===void 0)throw Error(he(407));n=n()}else{if(n=e(),Gt===null)throw Error(he(349));Br&30||P_(i,e,n)}r.memoizedState=n;var s={value:n,getSnapshot:e};return r.queue=s,yp(N_.bind(null,i,s,t),[t]),i.flags|=2048,Zo(9,L_.bind(null,i,s,n,e),void 0,null),n},useId:function(){var t=si(),e=Gt.identifierPrefix;if(Mt){var n=Ai,i=Ti;n=(i&~(1<<32-ei(i)-1)).toString(32)+n,e=":"+e+"R"+n,n=qo++,0<n&&(e+="H"+n.toString(32)),e+=":"}else n=ny++,e=":"+e+"r"+n.toString(32)+":";return t.memoizedState=e},unstable_isNewReconciler:!1},ay={readContext:zn,useCallback:z_,useContext:zn,useEffect:of,useImperativeHandle:B_,useInsertionEffect:O_,useLayoutEffect:F_,useMemo:H_,useReducer:Xc,useRef:U_,useState:function(){return Xc(Ko)},useDebugValue:af,useDeferredValue:function(t){var e=Hn();return V_(e,Ot.memoizedState,t)},useTransition:function(){var t=Xc(Ko)[0],e=Hn().memoizedState;return[t,e]},useMutableSource:b_,useSyncExternalStore:R_,useId:G_,unstable_isNewReconciler:!1},ly={readContext:zn,useCallback:z_,useContext:zn,useEffect:of,useImperativeHandle:B_,useInsertionEffect:O_,useLayoutEffect:F_,useMemo:H_,useReducer:$c,useRef:U_,useState:function(){return $c(Ko)},useDebugValue:af,useDeferredValue:function(t){var e=Hn();return Ot===null?e.memoizedState=t:V_(e,Ot.memoizedState,t)},useTransition:function(){var t=$c(Ko)[0],e=Hn().memoizedState;return[t,e]},useMutableSource:b_,useSyncExternalStore:R_,useId:G_,unstable_isNewReconciler:!1};function qn(t,e){if(t&&t.defaultProps){e=Tt({},e),t=t.defaultProps;for(var n in t)e[n]===void 0&&(e[n]=t[n]);return e}return e}function yd(t,e,n,i){e=t.memoizedState,n=n(i,e),n=n==null?e:Tt({},e,n),t.memoizedState=n,t.lanes===0&&(t.updateQueue.baseState=n)}var hc={isMounted:function(t){return(t=t._reactInternals)?Xr(t)===t:!1},enqueueSetState:function(t,e,n){t=t._reactInternals;var i=sn(),r=or(t),s=Ri(i,r);s.payload=e,n!=null&&(s.callback=n),e=rr(t,s,r),e!==null&&(ti(e,t,r,i),cl(e,t,r))},enqueueReplaceState:function(t,e,n){t=t._reactInternals;var i=sn(),r=or(t),s=Ri(i,r);s.tag=1,s.payload=e,n!=null&&(s.callback=n),e=rr(t,s,r),e!==null&&(ti(e,t,r,i),cl(e,t,r))},enqueueForceUpdate:function(t,e){t=t._reactInternals;var n=sn(),i=or(t),r=Ri(n,i);r.tag=2,e!=null&&(r.callback=e),e=rr(t,r,i),e!==null&&(ti(e,t,i,n),cl(e,t,i))}};function Sp(t,e,n,i,r,s,o){return t=t.stateNode,typeof t.shouldComponentUpdate=="function"?t.shouldComponentUpdate(i,s,o):e.prototype&&e.prototype.isPureReactComponent?!Go(n,i)||!Go(r,s):!0}function $_(t,e,n){var i=!1,r=dr,s=e.contextType;return typeof s=="object"&&s!==null?s=zn(s):(r=pn(e)?Fr:en.current,i=e.contextTypes,s=(i=i!=null)?ks(t,r):dr),e=new e(n,s),t.memoizedState=e.state!==null&&e.state!==void 0?e.state:null,e.updater=hc,t.stateNode=e,e._reactInternals=t,i&&(t=t.stateNode,t.__reactInternalMemoizedUnmaskedChildContext=r,t.__reactInternalMemoizedMaskedChildContext=s),e}function Mp(t,e,n,i){t=e.state,typeof e.componentWillReceiveProps=="function"&&e.componentWillReceiveProps(n,i),typeof e.UNSAFE_componentWillReceiveProps=="function"&&e.UNSAFE_componentWillReceiveProps(n,i),e.state!==t&&hc.enqueueReplaceState(e,e.state,null)}function Sd(t,e,n,i){var r=t.stateNode;r.props=n,r.state=t.memoizedState,r.refs={},Jh(t);var s=e.contextType;typeof s=="object"&&s!==null?r.context=zn(s):(s=pn(e)?Fr:en.current,r.context=ks(t,s)),r.state=t.memoizedState,s=e.getDerivedStateFromProps,typeof s=="function"&&(yd(t,e,s,n),r.state=t.memoizedState),typeof e.getDerivedStateFromProps=="function"||typeof r.getSnapshotBeforeUpdate=="function"||typeof r.UNSAFE_componentWillMount!="function"&&typeof r.componentWillMount!="function"||(e=r.state,typeof r.componentWillMount=="function"&&r.componentWillMount(),typeof r.UNSAFE_componentWillMount=="function"&&r.UNSAFE_componentWillMount(),e!==r.state&&hc.enqueueReplaceState(r,r.state,null),Hl(t,n,r,i),r.state=t.memoizedState),typeof r.componentDidMount=="function"&&(t.flags|=4194308)}function Vs(t,e){try{var n="",i=e;do n+=O0(i),i=i.return;while(i);var r=n}catch(s){r=`
Error generating stack: `+s.message+`
`+s.stack}return{value:t,source:e,stack:r,digest:null}}function Yc(t,e,n){return{value:t,source:null,stack:n??null,digest:e??null}}function Md(t,e){try{console.error(e.value)}catch(n){setTimeout(function(){throw n})}}var cy=typeof WeakMap=="function"?WeakMap:Map;function Y_(t,e,n){n=Ri(-1,n),n.tag=3,n.payload={element:null};var i=e.value;return n.callback=function(){Xl||(Xl=!0,Nd=i),Md(t,e)},n}function q_(t,e,n){n=Ri(-1,n),n.tag=3;var i=t.type.getDerivedStateFromError;if(typeof i=="function"){var r=e.value;n.payload=function(){return i(r)},n.callback=function(){Md(t,e)}}var s=t.stateNode;return s!==null&&typeof s.componentDidCatch=="function"&&(n.callback=function(){Md(t,e),typeof i!="function"&&(sr===null?sr=new Set([this]):sr.add(this));var o=e.stack;this.componentDidCatch(e.value,{componentStack:o!==null?o:""})}),n}function Ep(t,e,n){var i=t.pingCache;if(i===null){i=t.pingCache=new cy;var r=new Set;i.set(e,r)}else r=i.get(e),r===void 0&&(r=new Set,i.set(e,r));r.has(n)||(r.add(n),t=Ey.bind(null,t,e,n),e.then(t,t))}function wp(t){do{var e;if((e=t.tag===13)&&(e=t.memoizedState,e=e!==null?e.dehydrated!==null:!0),e)return t;t=t.return}while(t!==null);return null}function Tp(t,e,n,i,r){return t.mode&1?(t.flags|=65536,t.lanes=r,t):(t===e?t.flags|=65536:(t.flags|=128,n.flags|=131072,n.flags&=-52805,n.tag===1&&(n.alternate===null?n.tag=17:(e=Ri(-1,1),e.tag=2,rr(n,e,1))),n.lanes|=1),t)}var uy=Oi.ReactCurrentOwner,hn=!1;function rn(t,e,n,i){e.child=t===null?w_(e,null,n,i):zs(e,t.child,n,i)}function Ap(t,e,n,i,r){n=n.render;var s=e.ref;return Ls(e,r),i=rf(t,e,n,i,s,r),n=sf(),t!==null&&!hn?(e.updateQueue=t.updateQueue,e.flags&=-2053,t.lanes&=~r,Ii(t,e,r)):(Mt&&n&&Wh(e),e.flags|=1,rn(t,e,i,r),e.child)}function Cp(t,e,n,i,r){if(t===null){var s=n.type;return typeof s=="function"&&!mf(s)&&s.defaultProps===void 0&&n.compare===null&&n.defaultProps===void 0?(e.tag=15,e.type=s,K_(t,e,s,i,r)):(t=ml(n.type,null,i,e,e.mode,r),t.ref=e.ref,t.return=e,e.child=t)}if(s=t.child,!(t.lanes&r)){var o=s.memoizedProps;if(n=n.compare,n=n!==null?n:Go,n(o,i)&&t.ref===e.ref)return Ii(t,e,r)}return e.flags|=1,t=ar(s,i),t.ref=e.ref,t.return=e,e.child=t}function K_(t,e,n,i,r){if(t!==null){var s=t.memoizedProps;if(Go(s,i)&&t.ref===e.ref)if(hn=!1,e.pendingProps=i=s,(t.lanes&r)!==0)t.flags&131072&&(hn=!0);else return e.lanes=t.lanes,Ii(t,e,r)}return Ed(t,e,n,i,r)}function Z_(t,e,n){var i=e.pendingProps,r=i.children,s=t!==null?t.memoizedState:null;if(i.mode==="hidden")if(!(e.mode&1))e.memoizedState={baseLanes:0,cachePool:null,transitions:null},gt(ws,En),En|=n;else{if(!(n&1073741824))return t=s!==null?s.baseLanes|n:n,e.lanes=e.childLanes=1073741824,e.memoizedState={baseLanes:t,cachePool:null,transitions:null},e.updateQueue=null,gt(ws,En),En|=t,null;e.memoizedState={baseLanes:0,cachePool:null,transitions:null},i=s!==null?s.baseLanes:n,gt(ws,En),En|=i}else s!==null?(i=s.baseLanes|n,e.memoizedState=null):i=n,gt(ws,En),En|=i;return rn(t,e,r,n),e.child}function J_(t,e){var n=e.ref;(t===null&&n!==null||t!==null&&t.ref!==n)&&(e.flags|=512,e.flags|=2097152)}function Ed(t,e,n,i,r){var s=pn(n)?Fr:en.current;return s=ks(e,s),Ls(e,r),n=rf(t,e,n,i,s,r),i=sf(),t!==null&&!hn?(e.updateQueue=t.updateQueue,e.flags&=-2053,t.lanes&=~r,Ii(t,e,r)):(Mt&&i&&Wh(e),e.flags|=1,rn(t,e,n,r),e.child)}function bp(t,e,n,i,r){if(pn(n)){var s=!0;Ol(e)}else s=!1;if(Ls(e,r),e.stateNode===null)hl(t,e),$_(e,n,i),Sd(e,n,i,r),i=!0;else if(t===null){var o=e.stateNode,a=e.memoizedProps;o.props=a;var l=o.context,c=n.contextType;typeof c=="object"&&c!==null?c=zn(c):(c=pn(n)?Fr:en.current,c=ks(e,c));var d=n.getDerivedStateFromProps,h=typeof d=="function"||typeof o.getSnapshotBeforeUpdate=="function";h||typeof o.UNSAFE_componentWillReceiveProps!="function"&&typeof o.componentWillReceiveProps!="function"||(a!==i||l!==c)&&Mp(e,o,i,c),$i=!1;var f=e.memoizedState;o.state=f,Hl(e,i,o,r),l=e.memoizedState,a!==i||f!==l||fn.current||$i?(typeof d=="function"&&(yd(e,n,d,i),l=e.memoizedState),(a=$i||Sp(e,n,a,i,f,l,c))?(h||typeof o.UNSAFE_componentWillMount!="function"&&typeof o.componentWillMount!="function"||(typeof o.componentWillMount=="function"&&o.componentWillMount(),typeof o.UNSAFE_componentWillMount=="function"&&o.UNSAFE_componentWillMount()),typeof o.componentDidMount=="function"&&(e.flags|=4194308)):(typeof o.componentDidMount=="function"&&(e.flags|=4194308),e.memoizedProps=i,e.memoizedState=l),o.props=i,o.state=l,o.context=c,i=a):(typeof o.componentDidMount=="function"&&(e.flags|=4194308),i=!1)}else{o=e.stateNode,A_(t,e),a=e.memoizedProps,c=e.type===e.elementType?a:qn(e.type,a),o.props=c,h=e.pendingProps,f=o.context,l=n.contextType,typeof l=="object"&&l!==null?l=zn(l):(l=pn(n)?Fr:en.current,l=ks(e,l));var p=n.getDerivedStateFromProps;(d=typeof p=="function"||typeof o.getSnapshotBeforeUpdate=="function")||typeof o.UNSAFE_componentWillReceiveProps!="function"&&typeof o.componentWillReceiveProps!="function"||(a!==h||f!==l)&&Mp(e,o,i,l),$i=!1,f=e.memoizedState,o.state=f,Hl(e,i,o,r);var g=e.memoizedState;a!==h||f!==g||fn.current||$i?(typeof p=="function"&&(yd(e,n,p,i),g=e.memoizedState),(c=$i||Sp(e,n,c,i,f,g,l)||!1)?(d||typeof o.UNSAFE_componentWillUpdate!="function"&&typeof o.componentWillUpdate!="function"||(typeof o.componentWillUpdate=="function"&&o.componentWillUpdate(i,g,l),typeof o.UNSAFE_componentWillUpdate=="function"&&o.UNSAFE_componentWillUpdate(i,g,l)),typeof o.componentDidUpdate=="function"&&(e.flags|=4),typeof o.getSnapshotBeforeUpdate=="function"&&(e.flags|=1024)):(typeof o.componentDidUpdate!="function"||a===t.memoizedProps&&f===t.memoizedState||(e.flags|=4),typeof o.getSnapshotBeforeUpdate!="function"||a===t.memoizedProps&&f===t.memoizedState||(e.flags|=1024),e.memoizedProps=i,e.memoizedState=g),o.props=i,o.state=g,o.context=l,i=c):(typeof o.componentDidUpdate!="function"||a===t.memoizedProps&&f===t.memoizedState||(e.flags|=4),typeof o.getSnapshotBeforeUpdate!="function"||a===t.memoizedProps&&f===t.memoizedState||(e.flags|=1024),i=!1)}return wd(t,e,n,i,s,r)}function wd(t,e,n,i,r,s){J_(t,e);var o=(e.flags&128)!==0;if(!i&&!o)return r&&fp(e,n,!1),Ii(t,e,s);i=e.stateNode,uy.current=e;var a=o&&typeof n.getDerivedStateFromError!="function"?null:i.render();return e.flags|=1,t!==null&&o?(e.child=zs(e,t.child,null,s),e.child=zs(e,null,a,s)):rn(t,e,a,s),e.memoizedState=i.state,r&&fp(e,n,!0),e.child}function Q_(t){var e=t.stateNode;e.pendingContext?hp(t,e.pendingContext,e.pendingContext!==e.context):e.context&&hp(t,e.context,!1),Qh(t,e.containerInfo)}function Rp(t,e,n,i,r){return Bs(),$h(r),e.flags|=256,rn(t,e,n,i),e.child}var Td={dehydrated:null,treeContext:null,retryLane:0};function Ad(t){return{baseLanes:t,cachePool:null,transitions:null}}function ev(t,e,n){var i=e.pendingProps,r=Et.current,s=!1,o=(e.flags&128)!==0,a;if((a=o)||(a=t!==null&&t.memoizedState===null?!1:(r&2)!==0),a?(s=!0,e.flags&=-129):(t===null||t.memoizedState!==null)&&(r|=1),gt(Et,r&1),t===null)return vd(e),t=e.memoizedState,t!==null&&(t=t.dehydrated,t!==null)?(e.mode&1?t.data==="$!"?e.lanes=8:e.lanes=1073741824:e.lanes=1,null):(o=i.children,t=i.fallback,s?(i=e.mode,s=e.child,o={mode:"hidden",children:o},!(i&1)&&s!==null?(s.childLanes=0,s.pendingProps=o):s=mc(o,i,0,null),t=Or(t,i,n,null),s.return=e,t.return=e,s.sibling=t,e.child=s,e.child.memoizedState=Ad(n),e.memoizedState=Td,t):lf(e,o));if(r=t.memoizedState,r!==null&&(a=r.dehydrated,a!==null))return dy(t,e,o,i,a,r,n);if(s){s=i.fallback,o=e.mode,r=t.child,a=r.sibling;var l={mode:"hidden",children:i.children};return!(o&1)&&e.child!==r?(i=e.child,i.childLanes=0,i.pendingProps=l,e.deletions=null):(i=ar(r,l),i.subtreeFlags=r.subtreeFlags&14680064),a!==null?s=ar(a,s):(s=Or(s,o,n,null),s.flags|=2),s.return=e,i.return=e,i.sibling=s,e.child=i,i=s,s=e.child,o=t.child.memoizedState,o=o===null?Ad(n):{baseLanes:o.baseLanes|n,cachePool:null,transitions:o.transitions},s.memoizedState=o,s.childLanes=t.childLanes&~n,e.memoizedState=Td,i}return s=t.child,t=s.sibling,i=ar(s,{mode:"visible",children:i.children}),!(e.mode&1)&&(i.lanes=n),i.return=e,i.sibling=null,t!==null&&(n=e.deletions,n===null?(e.deletions=[t],e.flags|=16):n.push(t)),e.child=i,e.memoizedState=null,i}function lf(t,e){return e=mc({mode:"visible",children:e},t.mode,0,null),e.return=t,t.child=e}function Ca(t,e,n,i){return i!==null&&$h(i),zs(e,t.child,null,n),t=lf(e,e.pendingProps.children),t.flags|=2,e.memoizedState=null,t}function dy(t,e,n,i,r,s,o){if(n)return e.flags&256?(e.flags&=-257,i=Yc(Error(he(422))),Ca(t,e,o,i)):e.memoizedState!==null?(e.child=t.child,e.flags|=128,null):(s=i.fallback,r=e.mode,i=mc({mode:"visible",children:i.children},r,0,null),s=Or(s,r,o,null),s.flags|=2,i.return=e,s.return=e,i.sibling=s,e.child=i,e.mode&1&&zs(e,t.child,null,o),e.child.memoizedState=Ad(o),e.memoizedState=Td,s);if(!(e.mode&1))return Ca(t,e,o,null);if(r.data==="$!"){if(i=r.nextSibling&&r.nextSibling.dataset,i)var a=i.dgst;return i=a,s=Error(he(419)),i=Yc(s,i,void 0),Ca(t,e,o,i)}if(a=(o&t.childLanes)!==0,hn||a){if(i=Gt,i!==null){switch(o&-o){case 4:r=2;break;case 16:r=8;break;case 64:case 128:case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:case 262144:case 524288:case 1048576:case 2097152:case 4194304:case 8388608:case 16777216:case 33554432:case 67108864:r=32;break;case 536870912:r=268435456;break;default:r=0}r=r&(i.suspendedLanes|o)?0:r,r!==0&&r!==s.retryLane&&(s.retryLane=r,Di(t,r),ti(i,t,r,-1))}return pf(),i=Yc(Error(he(421))),Ca(t,e,o,i)}return r.data==="$?"?(e.flags|=128,e.child=t.child,e=wy.bind(null,t),r._reactRetry=e,null):(t=s.treeContext,wn=ir(r.nextSibling),An=e,Mt=!0,Zn=null,t!==null&&(Un[On++]=Ti,Un[On++]=Ai,Un[On++]=kr,Ti=t.id,Ai=t.overflow,kr=e),e=lf(e,i.children),e.flags|=4096,e)}function Pp(t,e,n){t.lanes|=e;var i=t.alternate;i!==null&&(i.lanes|=e),xd(t.return,e,n)}function qc(t,e,n,i,r){var s=t.memoizedState;s===null?t.memoizedState={isBackwards:e,rendering:null,renderingStartTime:0,last:i,tail:n,tailMode:r}:(s.isBackwards=e,s.rendering=null,s.renderingStartTime=0,s.last=i,s.tail=n,s.tailMode=r)}function tv(t,e,n){var i=e.pendingProps,r=i.revealOrder,s=i.tail;if(rn(t,e,i.children,n),i=Et.current,i&2)i=i&1|2,e.flags|=128;else{if(t!==null&&t.flags&128)e:for(t=e.child;t!==null;){if(t.tag===13)t.memoizedState!==null&&Pp(t,n,e);else if(t.tag===19)Pp(t,n,e);else if(t.child!==null){t.child.return=t,t=t.child;continue}if(t===e)break e;for(;t.sibling===null;){if(t.return===null||t.return===e)break e;t=t.return}t.sibling.return=t.return,t=t.sibling}i&=1}if(gt(Et,i),!(e.mode&1))e.memoizedState=null;else switch(r){case"forwards":for(n=e.child,r=null;n!==null;)t=n.alternate,t!==null&&Vl(t)===null&&(r=n),n=n.sibling;n=r,n===null?(r=e.child,e.child=null):(r=n.sibling,n.sibling=null),qc(e,!1,r,n,s);break;case"backwards":for(n=null,r=e.child,e.child=null;r!==null;){if(t=r.alternate,t!==null&&Vl(t)===null){e.child=r;break}t=r.sibling,r.sibling=n,n=r,r=t}qc(e,!0,n,null,s);break;case"together":qc(e,!1,null,null,void 0);break;default:e.memoizedState=null}return e.child}function hl(t,e){!(e.mode&1)&&t!==null&&(t.alternate=null,e.alternate=null,e.flags|=2)}function Ii(t,e,n){if(t!==null&&(e.dependencies=t.dependencies),zr|=e.lanes,!(n&e.childLanes))return null;if(t!==null&&e.child!==t.child)throw Error(he(153));if(e.child!==null){for(t=e.child,n=ar(t,t.pendingProps),e.child=n,n.return=e;t.sibling!==null;)t=t.sibling,n=n.sibling=ar(t,t.pendingProps),n.return=e;n.sibling=null}return e.child}function hy(t,e,n){switch(e.tag){case 3:Q_(e),Bs();break;case 5:C_(e);break;case 1:pn(e.type)&&Ol(e);break;case 4:Qh(e,e.stateNode.containerInfo);break;case 10:var i=e.type._context,r=e.memoizedProps.value;gt(Bl,i._currentValue),i._currentValue=r;break;case 13:if(i=e.memoizedState,i!==null)return i.dehydrated!==null?(gt(Et,Et.current&1),e.flags|=128,null):n&e.child.childLanes?ev(t,e,n):(gt(Et,Et.current&1),t=Ii(t,e,n),t!==null?t.sibling:null);gt(Et,Et.current&1);break;case 19:if(i=(n&e.childLanes)!==0,t.flags&128){if(i)return tv(t,e,n);e.flags|=128}if(r=e.memoizedState,r!==null&&(r.rendering=null,r.tail=null,r.lastEffect=null),gt(Et,Et.current),i)break;return null;case 22:case 23:return e.lanes=0,Z_(t,e,n)}return Ii(t,e,n)}var nv,Cd,iv,rv;nv=function(t,e){for(var n=e.child;n!==null;){if(n.tag===5||n.tag===6)t.appendChild(n.stateNode);else if(n.tag!==4&&n.child!==null){n.child.return=n,n=n.child;continue}if(n===e)break;for(;n.sibling===null;){if(n.return===null||n.return===e)return;n=n.return}n.sibling.return=n.return,n=n.sibling}};Cd=function(){};iv=function(t,e,n,i){var r=t.memoizedProps;if(r!==i){t=e.stateNode,Nr(ui.current);var s=null;switch(n){case"input":r=qu(t,r),i=qu(t,i),s=[];break;case"select":r=Tt({},r,{value:void 0}),i=Tt({},i,{value:void 0}),s=[];break;case"textarea":r=Ju(t,r),i=Ju(t,i),s=[];break;default:typeof r.onClick!="function"&&typeof i.onClick=="function"&&(t.onclick=Il)}ed(n,i);var o;n=null;for(c in r)if(!i.hasOwnProperty(c)&&r.hasOwnProperty(c)&&r[c]!=null)if(c==="style"){var a=r[c];for(o in a)a.hasOwnProperty(o)&&(n||(n={}),n[o]="")}else c!=="dangerouslySetInnerHTML"&&c!=="children"&&c!=="suppressContentEditableWarning"&&c!=="suppressHydrationWarning"&&c!=="autoFocus"&&(Oo.hasOwnProperty(c)?s||(s=[]):(s=s||[]).push(c,null));for(c in i){var l=i[c];if(a=r!=null?r[c]:void 0,i.hasOwnProperty(c)&&l!==a&&(l!=null||a!=null))if(c==="style")if(a){for(o in a)!a.hasOwnProperty(o)||l&&l.hasOwnProperty(o)||(n||(n={}),n[o]="");for(o in l)l.hasOwnProperty(o)&&a[o]!==l[o]&&(n||(n={}),n[o]=l[o])}else n||(s||(s=[]),s.push(c,n)),n=l;else c==="dangerouslySetInnerHTML"?(l=l?l.__html:void 0,a=a?a.__html:void 0,l!=null&&a!==l&&(s=s||[]).push(c,l)):c==="children"?typeof l!="string"&&typeof l!="number"||(s=s||[]).push(c,""+l):c!=="suppressContentEditableWarning"&&c!=="suppressHydrationWarning"&&(Oo.hasOwnProperty(c)?(l!=null&&c==="onScroll"&&_t("scroll",t),s||a===l||(s=[])):(s=s||[]).push(c,l))}n&&(s=s||[]).push("style",n);var c=s;(e.updateQueue=c)&&(e.flags|=4)}};rv=function(t,e,n,i){n!==i&&(e.flags|=4)};function co(t,e){if(!Mt)switch(t.tailMode){case"hidden":e=t.tail;for(var n=null;e!==null;)e.alternate!==null&&(n=e),e=e.sibling;n===null?t.tail=null:n.sibling=null;break;case"collapsed":n=t.tail;for(var i=null;n!==null;)n.alternate!==null&&(i=n),n=n.sibling;i===null?e||t.tail===null?t.tail=null:t.tail.sibling=null:i.sibling=null}}function Kt(t){var e=t.alternate!==null&&t.alternate.child===t.child,n=0,i=0;if(e)for(var r=t.child;r!==null;)n|=r.lanes|r.childLanes,i|=r.subtreeFlags&14680064,i|=r.flags&14680064,r.return=t,r=r.sibling;else for(r=t.child;r!==null;)n|=r.lanes|r.childLanes,i|=r.subtreeFlags,i|=r.flags,r.return=t,r=r.sibling;return t.subtreeFlags|=i,t.childLanes=n,e}function fy(t,e,n){var i=e.pendingProps;switch(Xh(e),e.tag){case 2:case 16:case 15:case 0:case 11:case 7:case 8:case 12:case 9:case 14:return Kt(e),null;case 1:return pn(e.type)&&Ul(),Kt(e),null;case 3:return i=e.stateNode,Hs(),vt(fn),vt(en),tf(),i.pendingContext&&(i.context=i.pendingContext,i.pendingContext=null),(t===null||t.child===null)&&(Ta(e)?e.flags|=4:t===null||t.memoizedState.isDehydrated&&!(e.flags&256)||(e.flags|=1024,Zn!==null&&(Ud(Zn),Zn=null))),Cd(t,e),Kt(e),null;case 5:ef(e);var r=Nr(Yo.current);if(n=e.type,t!==null&&e.stateNode!=null)iv(t,e,n,i,r),t.ref!==e.ref&&(e.flags|=512,e.flags|=2097152);else{if(!i){if(e.stateNode===null)throw Error(he(166));return Kt(e),null}if(t=Nr(ui.current),Ta(e)){i=e.stateNode,n=e.type;var s=e.memoizedProps;switch(i[ai]=e,i[Xo]=s,t=(e.mode&1)!==0,n){case"dialog":_t("cancel",i),_t("close",i);break;case"iframe":case"object":case"embed":_t("load",i);break;case"video":case"audio":for(r=0;r<So.length;r++)_t(So[r],i);break;case"source":_t("error",i);break;case"img":case"image":case"link":_t("error",i),_t("load",i);break;case"details":_t("toggle",i);break;case"input":Bf(i,s),_t("invalid",i);break;case"select":i._wrapperState={wasMultiple:!!s.multiple},_t("invalid",i);break;case"textarea":Hf(i,s),_t("invalid",i)}ed(n,s),r=null;for(var o in s)if(s.hasOwnProperty(o)){var a=s[o];o==="children"?typeof a=="string"?i.textContent!==a&&(s.suppressHydrationWarning!==!0&&wa(i.textContent,a,t),r=["children",a]):typeof a=="number"&&i.textContent!==""+a&&(s.suppressHydrationWarning!==!0&&wa(i.textContent,a,t),r=["children",""+a]):Oo.hasOwnProperty(o)&&a!=null&&o==="onScroll"&&_t("scroll",i)}switch(n){case"input":ga(i),zf(i,s,!0);break;case"textarea":ga(i),Vf(i);break;case"select":case"option":break;default:typeof s.onClick=="function"&&(i.onclick=Il)}i=r,e.updateQueue=i,i!==null&&(e.flags|=4)}else{o=r.nodeType===9?r:r.ownerDocument,t==="http://www.w3.org/1999/xhtml"&&(t=Ng(n)),t==="http://www.w3.org/1999/xhtml"?n==="script"?(t=o.createElement("div"),t.innerHTML="<script><\/script>",t=t.removeChild(t.firstChild)):typeof i.is=="string"?t=o.createElement(n,{is:i.is}):(t=o.createElement(n),n==="select"&&(o=t,i.multiple?o.multiple=!0:i.size&&(o.size=i.size))):t=o.createElementNS(t,n),t[ai]=e,t[Xo]=i,nv(t,e,!1,!1),e.stateNode=t;e:{switch(o=td(n,i),n){case"dialog":_t("cancel",t),_t("close",t),r=i;break;case"iframe":case"object":case"embed":_t("load",t),r=i;break;case"video":case"audio":for(r=0;r<So.length;r++)_t(So[r],t);r=i;break;case"source":_t("error",t),r=i;break;case"img":case"image":case"link":_t("error",t),_t("load",t),r=i;break;case"details":_t("toggle",t),r=i;break;case"input":Bf(t,i),r=qu(t,i),_t("invalid",t);break;case"option":r=i;break;case"select":t._wrapperState={wasMultiple:!!i.multiple},r=Tt({},i,{value:void 0}),_t("invalid",t);break;case"textarea":Hf(t,i),r=Ju(t,i),_t("invalid",t);break;default:r=i}ed(n,r),a=r;for(s in a)if(a.hasOwnProperty(s)){var l=a[s];s==="style"?Ug(t,l):s==="dangerouslySetInnerHTML"?(l=l?l.__html:void 0,l!=null&&Dg(t,l)):s==="children"?typeof l=="string"?(n!=="textarea"||l!=="")&&Fo(t,l):typeof l=="number"&&Fo(t,""+l):s!=="suppressContentEditableWarning"&&s!=="suppressHydrationWarning"&&s!=="autoFocus"&&(Oo.hasOwnProperty(s)?l!=null&&s==="onScroll"&&_t("scroll",t):l!=null&&Lh(t,s,l,o))}switch(n){case"input":ga(t),zf(t,i,!1);break;case"textarea":ga(t),Vf(t);break;case"option":i.value!=null&&t.setAttribute("value",""+ur(i.value));break;case"select":t.multiple=!!i.multiple,s=i.value,s!=null?Cs(t,!!i.multiple,s,!1):i.defaultValue!=null&&Cs(t,!!i.multiple,i.defaultValue,!0);break;default:typeof r.onClick=="function"&&(t.onclick=Il)}switch(n){case"button":case"input":case"select":case"textarea":i=!!i.autoFocus;break e;case"img":i=!0;break e;default:i=!1}}i&&(e.flags|=4)}e.ref!==null&&(e.flags|=512,e.flags|=2097152)}return Kt(e),null;case 6:if(t&&e.stateNode!=null)rv(t,e,t.memoizedProps,i);else{if(typeof i!="string"&&e.stateNode===null)throw Error(he(166));if(n=Nr(Yo.current),Nr(ui.current),Ta(e)){if(i=e.stateNode,n=e.memoizedProps,i[ai]=e,(s=i.nodeValue!==n)&&(t=An,t!==null))switch(t.tag){case 3:wa(i.nodeValue,n,(t.mode&1)!==0);break;case 5:t.memoizedProps.suppressHydrationWarning!==!0&&wa(i.nodeValue,n,(t.mode&1)!==0)}s&&(e.flags|=4)}else i=(n.nodeType===9?n:n.ownerDocument).createTextNode(i),i[ai]=e,e.stateNode=i}return Kt(e),null;case 13:if(vt(Et),i=e.memoizedState,t===null||t.memoizedState!==null&&t.memoizedState.dehydrated!==null){if(Mt&&wn!==null&&e.mode&1&&!(e.flags&128))M_(),Bs(),e.flags|=98560,s=!1;else if(s=Ta(e),i!==null&&i.dehydrated!==null){if(t===null){if(!s)throw Error(he(318));if(s=e.memoizedState,s=s!==null?s.dehydrated:null,!s)throw Error(he(317));s[ai]=e}else Bs(),!(e.flags&128)&&(e.memoizedState=null),e.flags|=4;Kt(e),s=!1}else Zn!==null&&(Ud(Zn),Zn=null),s=!0;if(!s)return e.flags&65536?e:null}return e.flags&128?(e.lanes=n,e):(i=i!==null,i!==(t!==null&&t.memoizedState!==null)&&i&&(e.child.flags|=8192,e.mode&1&&(t===null||Et.current&1?Ft===0&&(Ft=3):pf())),e.updateQueue!==null&&(e.flags|=4),Kt(e),null);case 4:return Hs(),Cd(t,e),t===null&&jo(e.stateNode.containerInfo),Kt(e),null;case 10:return Kh(e.type._context),Kt(e),null;case 17:return pn(e.type)&&Ul(),Kt(e),null;case 19:if(vt(Et),s=e.memoizedState,s===null)return Kt(e),null;if(i=(e.flags&128)!==0,o=s.rendering,o===null)if(i)co(s,!1);else{if(Ft!==0||t!==null&&t.flags&128)for(t=e.child;t!==null;){if(o=Vl(t),o!==null){for(e.flags|=128,co(s,!1),i=o.updateQueue,i!==null&&(e.updateQueue=i,e.flags|=4),e.subtreeFlags=0,i=n,n=e.child;n!==null;)s=n,t=i,s.flags&=14680066,o=s.alternate,o===null?(s.childLanes=0,s.lanes=t,s.child=null,s.subtreeFlags=0,s.memoizedProps=null,s.memoizedState=null,s.updateQueue=null,s.dependencies=null,s.stateNode=null):(s.childLanes=o.childLanes,s.lanes=o.lanes,s.child=o.child,s.subtreeFlags=0,s.deletions=null,s.memoizedProps=o.memoizedProps,s.memoizedState=o.memoizedState,s.updateQueue=o.updateQueue,s.type=o.type,t=o.dependencies,s.dependencies=t===null?null:{lanes:t.lanes,firstContext:t.firstContext}),n=n.sibling;return gt(Et,Et.current&1|2),e.child}t=t.sibling}s.tail!==null&&Pt()>Gs&&(e.flags|=128,i=!0,co(s,!1),e.lanes=4194304)}else{if(!i)if(t=Vl(o),t!==null){if(e.flags|=128,i=!0,n=t.updateQueue,n!==null&&(e.updateQueue=n,e.flags|=4),co(s,!0),s.tail===null&&s.tailMode==="hidden"&&!o.alternate&&!Mt)return Kt(e),null}else 2*Pt()-s.renderingStartTime>Gs&&n!==1073741824&&(e.flags|=128,i=!0,co(s,!1),e.lanes=4194304);s.isBackwards?(o.sibling=e.child,e.child=o):(n=s.last,n!==null?n.sibling=o:e.child=o,s.last=o)}return s.tail!==null?(e=s.tail,s.rendering=e,s.tail=e.sibling,s.renderingStartTime=Pt(),e.sibling=null,n=Et.current,gt(Et,i?n&1|2:n&1),e):(Kt(e),null);case 22:case 23:return ff(),i=e.memoizedState!==null,t!==null&&t.memoizedState!==null!==i&&(e.flags|=8192),i&&e.mode&1?En&1073741824&&(Kt(e),e.subtreeFlags&6&&(e.flags|=8192)):Kt(e),null;case 24:return null;case 25:return null}throw Error(he(156,e.tag))}function py(t,e){switch(Xh(e),e.tag){case 1:return pn(e.type)&&Ul(),t=e.flags,t&65536?(e.flags=t&-65537|128,e):null;case 3:return Hs(),vt(fn),vt(en),tf(),t=e.flags,t&65536&&!(t&128)?(e.flags=t&-65537|128,e):null;case 5:return ef(e),null;case 13:if(vt(Et),t=e.memoizedState,t!==null&&t.dehydrated!==null){if(e.alternate===null)throw Error(he(340));Bs()}return t=e.flags,t&65536?(e.flags=t&-65537|128,e):null;case 19:return vt(Et),null;case 4:return Hs(),null;case 10:return Kh(e.type._context),null;case 22:case 23:return ff(),null;case 24:return null;default:return null}}var ba=!1,Qt=!1,my=typeof WeakSet=="function"?WeakSet:Set,Ne=null;function Es(t,e){var n=t.ref;if(n!==null)if(typeof n=="function")try{n(null)}catch(i){bt(t,e,i)}else n.current=null}function bd(t,e,n){try{n()}catch(i){bt(t,e,i)}}var Lp=!1;function gy(t,e){if(dd=Ll,t=c_(),jh(t)){if("selectionStart"in t)var n={start:t.selectionStart,end:t.selectionEnd};else e:{n=(n=t.ownerDocument)&&n.defaultView||window;var i=n.getSelection&&n.getSelection();if(i&&i.rangeCount!==0){n=i.anchorNode;var r=i.anchorOffset,s=i.focusNode;i=i.focusOffset;try{n.nodeType,s.nodeType}catch{n=null;break e}var o=0,a=-1,l=-1,c=0,d=0,h=t,f=null;t:for(;;){for(var p;h!==n||r!==0&&h.nodeType!==3||(a=o+r),h!==s||i!==0&&h.nodeType!==3||(l=o+i),h.nodeType===3&&(o+=h.nodeValue.length),(p=h.firstChild)!==null;)f=h,h=p;for(;;){if(h===t)break t;if(f===n&&++c===r&&(a=o),f===s&&++d===i&&(l=o),(p=h.nextSibling)!==null)break;h=f,f=h.parentNode}h=p}n=a===-1||l===-1?null:{start:a,end:l}}else n=null}n=n||{start:0,end:0}}else n=null;for(hd={focusedElem:t,selectionRange:n},Ll=!1,Ne=e;Ne!==null;)if(e=Ne,t=e.child,(e.subtreeFlags&1028)!==0&&t!==null)t.return=e,Ne=t;else for(;Ne!==null;){e=Ne;try{var g=e.alternate;if(e.flags&1024)switch(e.tag){case 0:case 11:case 15:break;case 1:if(g!==null){var x=g.memoizedProps,m=g.memoizedState,u=e.stateNode,_=u.getSnapshotBeforeUpdate(e.elementType===e.type?x:qn(e.type,x),m);u.__reactInternalSnapshotBeforeUpdate=_}break;case 3:var v=e.stateNode.containerInfo;v.nodeType===1?v.textContent="":v.nodeType===9&&v.documentElement&&v.removeChild(v.documentElement);break;case 5:case 6:case 4:case 17:break;default:throw Error(he(163))}}catch(M){bt(e,e.return,M)}if(t=e.sibling,t!==null){t.return=e.return,Ne=t;break}Ne=e.return}return g=Lp,Lp=!1,g}function Po(t,e,n){var i=e.updateQueue;if(i=i!==null?i.lastEffect:null,i!==null){var r=i=i.next;do{if((r.tag&t)===t){var s=r.destroy;r.destroy=void 0,s!==void 0&&bd(e,n,s)}r=r.next}while(r!==i)}}function fc(t,e){if(e=e.updateQueue,e=e!==null?e.lastEffect:null,e!==null){var n=e=e.next;do{if((n.tag&t)===t){var i=n.create;n.destroy=i()}n=n.next}while(n!==e)}}function Rd(t){var e=t.ref;if(e!==null){var n=t.stateNode;switch(t.tag){case 5:t=n;break;default:t=n}typeof e=="function"?e(t):e.current=t}}function sv(t){var e=t.alternate;e!==null&&(t.alternate=null,sv(e)),t.child=null,t.deletions=null,t.sibling=null,t.tag===5&&(e=t.stateNode,e!==null&&(delete e[ai],delete e[Xo],delete e[md],delete e[Jx],delete e[Qx])),t.stateNode=null,t.return=null,t.dependencies=null,t.memoizedProps=null,t.memoizedState=null,t.pendingProps=null,t.stateNode=null,t.updateQueue=null}function ov(t){return t.tag===5||t.tag===3||t.tag===4}function Np(t){e:for(;;){for(;t.sibling===null;){if(t.return===null||ov(t.return))return null;t=t.return}for(t.sibling.return=t.return,t=t.sibling;t.tag!==5&&t.tag!==6&&t.tag!==18;){if(t.flags&2||t.child===null||t.tag===4)continue e;t.child.return=t,t=t.child}if(!(t.flags&2))return t.stateNode}}function Pd(t,e,n){var i=t.tag;if(i===5||i===6)t=t.stateNode,e?n.nodeType===8?n.parentNode.insertBefore(t,e):n.insertBefore(t,e):(n.nodeType===8?(e=n.parentNode,e.insertBefore(t,n)):(e=n,e.appendChild(t)),n=n._reactRootContainer,n!=null||e.onclick!==null||(e.onclick=Il));else if(i!==4&&(t=t.child,t!==null))for(Pd(t,e,n),t=t.sibling;t!==null;)Pd(t,e,n),t=t.sibling}function Ld(t,e,n){var i=t.tag;if(i===5||i===6)t=t.stateNode,e?n.insertBefore(t,e):n.appendChild(t);else if(i!==4&&(t=t.child,t!==null))for(Ld(t,e,n),t=t.sibling;t!==null;)Ld(t,e,n),t=t.sibling}var Wt=null,Kn=!1;function ki(t,e,n){for(n=n.child;n!==null;)av(t,e,n),n=n.sibling}function av(t,e,n){if(ci&&typeof ci.onCommitFiberUnmount=="function")try{ci.onCommitFiberUnmount(sc,n)}catch{}switch(n.tag){case 5:Qt||Es(n,e);case 6:var i=Wt,r=Kn;Wt=null,ki(t,e,n),Wt=i,Kn=r,Wt!==null&&(Kn?(t=Wt,n=n.stateNode,t.nodeType===8?t.parentNode.removeChild(n):t.removeChild(n)):Wt.removeChild(n.stateNode));break;case 18:Wt!==null&&(Kn?(t=Wt,n=n.stateNode,t.nodeType===8?Vc(t.parentNode,n):t.nodeType===1&&Vc(t,n),Ho(t)):Vc(Wt,n.stateNode));break;case 4:i=Wt,r=Kn,Wt=n.stateNode.containerInfo,Kn=!0,ki(t,e,n),Wt=i,Kn=r;break;case 0:case 11:case 14:case 15:if(!Qt&&(i=n.updateQueue,i!==null&&(i=i.lastEffect,i!==null))){r=i=i.next;do{var s=r,o=s.destroy;s=s.tag,o!==void 0&&(s&2||s&4)&&bd(n,e,o),r=r.next}while(r!==i)}ki(t,e,n);break;case 1:if(!Qt&&(Es(n,e),i=n.stateNode,typeof i.componentWillUnmount=="function"))try{i.props=n.memoizedProps,i.state=n.memoizedState,i.componentWillUnmount()}catch(a){bt(n,e,a)}ki(t,e,n);break;case 21:ki(t,e,n);break;case 22:n.mode&1?(Qt=(i=Qt)||n.memoizedState!==null,ki(t,e,n),Qt=i):ki(t,e,n);break;default:ki(t,e,n)}}function Dp(t){var e=t.updateQueue;if(e!==null){t.updateQueue=null;var n=t.stateNode;n===null&&(n=t.stateNode=new my),e.forEach(function(i){var r=Ty.bind(null,t,i);n.has(i)||(n.add(i),i.then(r,r))})}}function jn(t,e){var n=e.deletions;if(n!==null)for(var i=0;i<n.length;i++){var r=n[i];try{var s=t,o=e,a=o;e:for(;a!==null;){switch(a.tag){case 5:Wt=a.stateNode,Kn=!1;break e;case 3:Wt=a.stateNode.containerInfo,Kn=!0;break e;case 4:Wt=a.stateNode.containerInfo,Kn=!0;break e}a=a.return}if(Wt===null)throw Error(he(160));av(s,o,r),Wt=null,Kn=!1;var l=r.alternate;l!==null&&(l.return=null),r.return=null}catch(c){bt(r,e,c)}}if(e.subtreeFlags&12854)for(e=e.child;e!==null;)lv(e,t),e=e.sibling}function lv(t,e){var n=t.alternate,i=t.flags;switch(t.tag){case 0:case 11:case 14:case 15:if(jn(e,t),ri(t),i&4){try{Po(3,t,t.return),fc(3,t)}catch(x){bt(t,t.return,x)}try{Po(5,t,t.return)}catch(x){bt(t,t.return,x)}}break;case 1:jn(e,t),ri(t),i&512&&n!==null&&Es(n,n.return);break;case 5:if(jn(e,t),ri(t),i&512&&n!==null&&Es(n,n.return),t.flags&32){var r=t.stateNode;try{Fo(r,"")}catch(x){bt(t,t.return,x)}}if(i&4&&(r=t.stateNode,r!=null)){var s=t.memoizedProps,o=n!==null?n.memoizedProps:s,a=t.type,l=t.updateQueue;if(t.updateQueue=null,l!==null)try{a==="input"&&s.type==="radio"&&s.name!=null&&Pg(r,s),td(a,o);var c=td(a,s);for(o=0;o<l.length;o+=2){var d=l[o],h=l[o+1];d==="style"?Ug(r,h):d==="dangerouslySetInnerHTML"?Dg(r,h):d==="children"?Fo(r,h):Lh(r,d,h,c)}switch(a){case"input":Ku(r,s);break;case"textarea":Lg(r,s);break;case"select":var f=r._wrapperState.wasMultiple;r._wrapperState.wasMultiple=!!s.multiple;var p=s.value;p!=null?Cs(r,!!s.multiple,p,!1):f!==!!s.multiple&&(s.defaultValue!=null?Cs(r,!!s.multiple,s.defaultValue,!0):Cs(r,!!s.multiple,s.multiple?[]:"",!1))}r[Xo]=s}catch(x){bt(t,t.return,x)}}break;case 6:if(jn(e,t),ri(t),i&4){if(t.stateNode===null)throw Error(he(162));r=t.stateNode,s=t.memoizedProps;try{r.nodeValue=s}catch(x){bt(t,t.return,x)}}break;case 3:if(jn(e,t),ri(t),i&4&&n!==null&&n.memoizedState.isDehydrated)try{Ho(e.containerInfo)}catch(x){bt(t,t.return,x)}break;case 4:jn(e,t),ri(t);break;case 13:jn(e,t),ri(t),r=t.child,r.flags&8192&&(s=r.memoizedState!==null,r.stateNode.isHidden=s,!s||r.alternate!==null&&r.alternate.memoizedState!==null||(df=Pt())),i&4&&Dp(t);break;case 22:if(d=n!==null&&n.memoizedState!==null,t.mode&1?(Qt=(c=Qt)||d,jn(e,t),Qt=c):jn(e,t),ri(t),i&8192){if(c=t.memoizedState!==null,(t.stateNode.isHidden=c)&&!d&&t.mode&1)for(Ne=t,d=t.child;d!==null;){for(h=Ne=d;Ne!==null;){switch(f=Ne,p=f.child,f.tag){case 0:case 11:case 14:case 15:Po(4,f,f.return);break;case 1:Es(f,f.return);var g=f.stateNode;if(typeof g.componentWillUnmount=="function"){i=f,n=f.return;try{e=i,g.props=e.memoizedProps,g.state=e.memoizedState,g.componentWillUnmount()}catch(x){bt(i,n,x)}}break;case 5:Es(f,f.return);break;case 22:if(f.memoizedState!==null){Up(h);continue}}p!==null?(p.return=f,Ne=p):Up(h)}d=d.sibling}e:for(d=null,h=t;;){if(h.tag===5){if(d===null){d=h;try{r=h.stateNode,c?(s=r.style,typeof s.setProperty=="function"?s.setProperty("display","none","important"):s.display="none"):(a=h.stateNode,l=h.memoizedProps.style,o=l!=null&&l.hasOwnProperty("display")?l.display:null,a.style.display=Ig("display",o))}catch(x){bt(t,t.return,x)}}}else if(h.tag===6){if(d===null)try{h.stateNode.nodeValue=c?"":h.memoizedProps}catch(x){bt(t,t.return,x)}}else if((h.tag!==22&&h.tag!==23||h.memoizedState===null||h===t)&&h.child!==null){h.child.return=h,h=h.child;continue}if(h===t)break e;for(;h.sibling===null;){if(h.return===null||h.return===t)break e;d===h&&(d=null),h=h.return}d===h&&(d=null),h.sibling.return=h.return,h=h.sibling}}break;case 19:jn(e,t),ri(t),i&4&&Dp(t);break;case 21:break;default:jn(e,t),ri(t)}}function ri(t){var e=t.flags;if(e&2){try{e:{for(var n=t.return;n!==null;){if(ov(n)){var i=n;break e}n=n.return}throw Error(he(160))}switch(i.tag){case 5:var r=i.stateNode;i.flags&32&&(Fo(r,""),i.flags&=-33);var s=Np(t);Ld(t,s,r);break;case 3:case 4:var o=i.stateNode.containerInfo,a=Np(t);Pd(t,a,o);break;default:throw Error(he(161))}}catch(l){bt(t,t.return,l)}t.flags&=-3}e&4096&&(t.flags&=-4097)}function _y(t,e,n){Ne=t,cv(t)}function cv(t,e,n){for(var i=(t.mode&1)!==0;Ne!==null;){var r=Ne,s=r.child;if(r.tag===22&&i){var o=r.memoizedState!==null||ba;if(!o){var a=r.alternate,l=a!==null&&a.memoizedState!==null||Qt;a=ba;var c=Qt;if(ba=o,(Qt=l)&&!c)for(Ne=r;Ne!==null;)o=Ne,l=o.child,o.tag===22&&o.memoizedState!==null?Op(r):l!==null?(l.return=o,Ne=l):Op(r);for(;s!==null;)Ne=s,cv(s),s=s.sibling;Ne=r,ba=a,Qt=c}Ip(t)}else r.subtreeFlags&8772&&s!==null?(s.return=r,Ne=s):Ip(t)}}function Ip(t){for(;Ne!==null;){var e=Ne;if(e.flags&8772){var n=e.alternate;try{if(e.flags&8772)switch(e.tag){case 0:case 11:case 15:Qt||fc(5,e);break;case 1:var i=e.stateNode;if(e.flags&4&&!Qt)if(n===null)i.componentDidMount();else{var r=e.elementType===e.type?n.memoizedProps:qn(e.type,n.memoizedProps);i.componentDidUpdate(r,n.memoizedState,i.__reactInternalSnapshotBeforeUpdate)}var s=e.updateQueue;s!==null&&vp(e,s,i);break;case 3:var o=e.updateQueue;if(o!==null){if(n=null,e.child!==null)switch(e.child.tag){case 5:n=e.child.stateNode;break;case 1:n=e.child.stateNode}vp(e,o,n)}break;case 5:var a=e.stateNode;if(n===null&&e.flags&4){n=a;var l=e.memoizedProps;switch(e.type){case"button":case"input":case"select":case"textarea":l.autoFocus&&n.focus();break;case"img":l.src&&(n.src=l.src)}}break;case 6:break;case 4:break;case 12:break;case 13:if(e.memoizedState===null){var c=e.alternate;if(c!==null){var d=c.memoizedState;if(d!==null){var h=d.dehydrated;h!==null&&Ho(h)}}}break;case 19:case 17:case 21:case 22:case 23:case 25:break;default:throw Error(he(163))}Qt||e.flags&512&&Rd(e)}catch(f){bt(e,e.return,f)}}if(e===t){Ne=null;break}if(n=e.sibling,n!==null){n.return=e.return,Ne=n;break}Ne=e.return}}function Up(t){for(;Ne!==null;){var e=Ne;if(e===t){Ne=null;break}var n=e.sibling;if(n!==null){n.return=e.return,Ne=n;break}Ne=e.return}}function Op(t){for(;Ne!==null;){var e=Ne;try{switch(e.tag){case 0:case 11:case 15:var n=e.return;try{fc(4,e)}catch(l){bt(e,n,l)}break;case 1:var i=e.stateNode;if(typeof i.componentDidMount=="function"){var r=e.return;try{i.componentDidMount()}catch(l){bt(e,r,l)}}var s=e.return;try{Rd(e)}catch(l){bt(e,s,l)}break;case 5:var o=e.return;try{Rd(e)}catch(l){bt(e,o,l)}}}catch(l){bt(e,e.return,l)}if(e===t){Ne=null;break}var a=e.sibling;if(a!==null){a.return=e.return,Ne=a;break}Ne=e.return}}var vy=Math.ceil,Wl=Oi.ReactCurrentDispatcher,cf=Oi.ReactCurrentOwner,Bn=Oi.ReactCurrentBatchConfig,ot=0,Gt=null,It=null,Xt=0,En=0,ws=mr(0),Ft=0,Jo=null,zr=0,pc=0,uf=0,Lo=null,dn=null,df=0,Gs=1/0,Mi=null,Xl=!1,Nd=null,sr=null,Ra=!1,Qi=null,$l=0,No=0,Dd=null,fl=-1,pl=0;function sn(){return ot&6?Pt():fl!==-1?fl:fl=Pt()}function or(t){return t.mode&1?ot&2&&Xt!==0?Xt&-Xt:ty.transition!==null?(pl===0&&(pl=$g()),pl):(t=ht,t!==0||(t=window.event,t=t===void 0?16:e_(t.type)),t):1}function ti(t,e,n,i){if(50<No)throw No=0,Dd=null,Error(he(185));na(t,n,i),(!(ot&2)||t!==Gt)&&(t===Gt&&(!(ot&2)&&(pc|=n),Ft===4&&Ki(t,Xt)),mn(t,i),n===1&&ot===0&&!(e.mode&1)&&(Gs=Pt()+500,uc&&gr()))}function mn(t,e){var n=t.callbackNode;tx(t,e);var i=Pl(t,t===Gt?Xt:0);if(i===0)n!==null&&Wf(n),t.callbackNode=null,t.callbackPriority=0;else if(e=i&-i,t.callbackPriority!==e){if(n!=null&&Wf(n),e===1)t.tag===0?ey(Fp.bind(null,t)):x_(Fp.bind(null,t)),Kx(function(){!(ot&6)&&gr()}),n=null;else{switch(Yg(i)){case 1:n=Oh;break;case 4:n=Wg;break;case 16:n=Rl;break;case 536870912:n=Xg;break;default:n=Rl}n=_v(n,uv.bind(null,t))}t.callbackPriority=e,t.callbackNode=n}}function uv(t,e){if(fl=-1,pl=0,ot&6)throw Error(he(327));var n=t.callbackNode;if(Ns()&&t.callbackNode!==n)return null;var i=Pl(t,t===Gt?Xt:0);if(i===0)return null;if(i&30||i&t.expiredLanes||e)e=Yl(t,i);else{e=i;var r=ot;ot|=2;var s=hv();(Gt!==t||Xt!==e)&&(Mi=null,Gs=Pt()+500,Ur(t,e));do try{Sy();break}catch(a){dv(t,a)}while(!0);qh(),Wl.current=s,ot=r,It!==null?e=0:(Gt=null,Xt=0,e=Ft)}if(e!==0){if(e===2&&(r=od(t),r!==0&&(i=r,e=Id(t,r))),e===1)throw n=Jo,Ur(t,0),Ki(t,i),mn(t,Pt()),n;if(e===6)Ki(t,i);else{if(r=t.current.alternate,!(i&30)&&!xy(r)&&(e=Yl(t,i),e===2&&(s=od(t),s!==0&&(i=s,e=Id(t,s))),e===1))throw n=Jo,Ur(t,0),Ki(t,i),mn(t,Pt()),n;switch(t.finishedWork=r,t.finishedLanes=i,e){case 0:case 1:throw Error(he(345));case 2:Ar(t,dn,Mi);break;case 3:if(Ki(t,i),(i&130023424)===i&&(e=df+500-Pt(),10<e)){if(Pl(t,0)!==0)break;if(r=t.suspendedLanes,(r&i)!==i){sn(),t.pingedLanes|=t.suspendedLanes&r;break}t.timeoutHandle=pd(Ar.bind(null,t,dn,Mi),e);break}Ar(t,dn,Mi);break;case 4:if(Ki(t,i),(i&4194240)===i)break;for(e=t.eventTimes,r=-1;0<i;){var o=31-ei(i);s=1<<o,o=e[o],o>r&&(r=o),i&=~s}if(i=r,i=Pt()-i,i=(120>i?120:480>i?480:1080>i?1080:1920>i?1920:3e3>i?3e3:4320>i?4320:1960*vy(i/1960))-i,10<i){t.timeoutHandle=pd(Ar.bind(null,t,dn,Mi),i);break}Ar(t,dn,Mi);break;case 5:Ar(t,dn,Mi);break;default:throw Error(he(329))}}}return mn(t,Pt()),t.callbackNode===n?uv.bind(null,t):null}function Id(t,e){var n=Lo;return t.current.memoizedState.isDehydrated&&(Ur(t,e).flags|=256),t=Yl(t,e),t!==2&&(e=dn,dn=n,e!==null&&Ud(e)),t}function Ud(t){dn===null?dn=t:dn.push.apply(dn,t)}function xy(t){for(var e=t;;){if(e.flags&16384){var n=e.updateQueue;if(n!==null&&(n=n.stores,n!==null))for(var i=0;i<n.length;i++){var r=n[i],s=r.getSnapshot;r=r.value;try{if(!ii(s(),r))return!1}catch{return!1}}}if(n=e.child,e.subtreeFlags&16384&&n!==null)n.return=e,e=n;else{if(e===t)break;for(;e.sibling===null;){if(e.return===null||e.return===t)return!0;e=e.return}e.sibling.return=e.return,e=e.sibling}}return!0}function Ki(t,e){for(e&=~uf,e&=~pc,t.suspendedLanes|=e,t.pingedLanes&=~e,t=t.expirationTimes;0<e;){var n=31-ei(e),i=1<<n;t[n]=-1,e&=~i}}function Fp(t){if(ot&6)throw Error(he(327));Ns();var e=Pl(t,0);if(!(e&1))return mn(t,Pt()),null;var n=Yl(t,e);if(t.tag!==0&&n===2){var i=od(t);i!==0&&(e=i,n=Id(t,i))}if(n===1)throw n=Jo,Ur(t,0),Ki(t,e),mn(t,Pt()),n;if(n===6)throw Error(he(345));return t.finishedWork=t.current.alternate,t.finishedLanes=e,Ar(t,dn,Mi),mn(t,Pt()),null}function hf(t,e){var n=ot;ot|=1;try{return t(e)}finally{ot=n,ot===0&&(Gs=Pt()+500,uc&&gr())}}function Hr(t){Qi!==null&&Qi.tag===0&&!(ot&6)&&Ns();var e=ot;ot|=1;var n=Bn.transition,i=ht;try{if(Bn.transition=null,ht=1,t)return t()}finally{ht=i,Bn.transition=n,ot=e,!(ot&6)&&gr()}}function ff(){En=ws.current,vt(ws)}function Ur(t,e){t.finishedWork=null,t.finishedLanes=0;var n=t.timeoutHandle;if(n!==-1&&(t.timeoutHandle=-1,qx(n)),It!==null)for(n=It.return;n!==null;){var i=n;switch(Xh(i),i.tag){case 1:i=i.type.childContextTypes,i!=null&&Ul();break;case 3:Hs(),vt(fn),vt(en),tf();break;case 5:ef(i);break;case 4:Hs();break;case 13:vt(Et);break;case 19:vt(Et);break;case 10:Kh(i.type._context);break;case 22:case 23:ff()}n=n.return}if(Gt=t,It=t=ar(t.current,null),Xt=En=e,Ft=0,Jo=null,uf=pc=zr=0,dn=Lo=null,Lr!==null){for(e=0;e<Lr.length;e++)if(n=Lr[e],i=n.interleaved,i!==null){n.interleaved=null;var r=i.next,s=n.pending;if(s!==null){var o=s.next;s.next=r,i.next=o}n.pending=i}Lr=null}return t}function dv(t,e){do{var n=It;try{if(qh(),ul.current=jl,Gl){for(var i=wt.memoizedState;i!==null;){var r=i.queue;r!==null&&(r.pending=null),i=i.next}Gl=!1}if(Br=0,Vt=Ot=wt=null,Ro=!1,qo=0,cf.current=null,n===null||n.return===null){Ft=1,Jo=e,It=null;break}e:{var s=t,o=n.return,a=n,l=e;if(e=Xt,a.flags|=32768,l!==null&&typeof l=="object"&&typeof l.then=="function"){var c=l,d=a,h=d.tag;if(!(d.mode&1)&&(h===0||h===11||h===15)){var f=d.alternate;f?(d.updateQueue=f.updateQueue,d.memoizedState=f.memoizedState,d.lanes=f.lanes):(d.updateQueue=null,d.memoizedState=null)}var p=wp(o);if(p!==null){p.flags&=-257,Tp(p,o,a,s,e),p.mode&1&&Ep(s,c,e),e=p,l=c;var g=e.updateQueue;if(g===null){var x=new Set;x.add(l),e.updateQueue=x}else g.add(l);break e}else{if(!(e&1)){Ep(s,c,e),pf();break e}l=Error(he(426))}}else if(Mt&&a.mode&1){var m=wp(o);if(m!==null){!(m.flags&65536)&&(m.flags|=256),Tp(m,o,a,s,e),$h(Vs(l,a));break e}}s=l=Vs(l,a),Ft!==4&&(Ft=2),Lo===null?Lo=[s]:Lo.push(s),s=o;do{switch(s.tag){case 3:s.flags|=65536,e&=-e,s.lanes|=e;var u=Y_(s,l,e);_p(s,u);break e;case 1:a=l;var _=s.type,v=s.stateNode;if(!(s.flags&128)&&(typeof _.getDerivedStateFromError=="function"||v!==null&&typeof v.componentDidCatch=="function"&&(sr===null||!sr.has(v)))){s.flags|=65536,e&=-e,s.lanes|=e;var M=q_(s,a,e);_p(s,M);break e}}s=s.return}while(s!==null)}pv(n)}catch(R){e=R,It===n&&n!==null&&(It=n=n.return);continue}break}while(!0)}function hv(){var t=Wl.current;return Wl.current=jl,t===null?jl:t}function pf(){(Ft===0||Ft===3||Ft===2)&&(Ft=4),Gt===null||!(zr&268435455)&&!(pc&268435455)||Ki(Gt,Xt)}function Yl(t,e){var n=ot;ot|=2;var i=hv();(Gt!==t||Xt!==e)&&(Mi=null,Ur(t,e));do try{yy();break}catch(r){dv(t,r)}while(!0);if(qh(),ot=n,Wl.current=i,It!==null)throw Error(he(261));return Gt=null,Xt=0,Ft}function yy(){for(;It!==null;)fv(It)}function Sy(){for(;It!==null&&!X0();)fv(It)}function fv(t){var e=gv(t.alternate,t,En);t.memoizedProps=t.pendingProps,e===null?pv(t):It=e,cf.current=null}function pv(t){var e=t;do{var n=e.alternate;if(t=e.return,e.flags&32768){if(n=py(n,e),n!==null){n.flags&=32767,It=n;return}if(t!==null)t.flags|=32768,t.subtreeFlags=0,t.deletions=null;else{Ft=6,It=null;return}}else if(n=fy(n,e,En),n!==null){It=n;return}if(e=e.sibling,e!==null){It=e;return}It=e=t}while(e!==null);Ft===0&&(Ft=5)}function Ar(t,e,n){var i=ht,r=Bn.transition;try{Bn.transition=null,ht=1,My(t,e,n,i)}finally{Bn.transition=r,ht=i}return null}function My(t,e,n,i){do Ns();while(Qi!==null);if(ot&6)throw Error(he(327));n=t.finishedWork;var r=t.finishedLanes;if(n===null)return null;if(t.finishedWork=null,t.finishedLanes=0,n===t.current)throw Error(he(177));t.callbackNode=null,t.callbackPriority=0;var s=n.lanes|n.childLanes;if(nx(t,s),t===Gt&&(It=Gt=null,Xt=0),!(n.subtreeFlags&2064)&&!(n.flags&2064)||Ra||(Ra=!0,_v(Rl,function(){return Ns(),null})),s=(n.flags&15990)!==0,n.subtreeFlags&15990||s){s=Bn.transition,Bn.transition=null;var o=ht;ht=1;var a=ot;ot|=4,cf.current=null,gy(t,n),lv(n,t),Vx(hd),Ll=!!dd,hd=dd=null,t.current=n,_y(n),$0(),ot=a,ht=o,Bn.transition=s}else t.current=n;if(Ra&&(Ra=!1,Qi=t,$l=r),s=t.pendingLanes,s===0&&(sr=null),K0(n.stateNode),mn(t,Pt()),e!==null)for(i=t.onRecoverableError,n=0;n<e.length;n++)r=e[n],i(r.value,{componentStack:r.stack,digest:r.digest});if(Xl)throw Xl=!1,t=Nd,Nd=null,t;return $l&1&&t.tag!==0&&Ns(),s=t.pendingLanes,s&1?t===Dd?No++:(No=0,Dd=t):No=0,gr(),null}function Ns(){if(Qi!==null){var t=Yg($l),e=Bn.transition,n=ht;try{if(Bn.transition=null,ht=16>t?16:t,Qi===null)var i=!1;else{if(t=Qi,Qi=null,$l=0,ot&6)throw Error(he(331));var r=ot;for(ot|=4,Ne=t.current;Ne!==null;){var s=Ne,o=s.child;if(Ne.flags&16){var a=s.deletions;if(a!==null){for(var l=0;l<a.length;l++){var c=a[l];for(Ne=c;Ne!==null;){var d=Ne;switch(d.tag){case 0:case 11:case 15:Po(8,d,s)}var h=d.child;if(h!==null)h.return=d,Ne=h;else for(;Ne!==null;){d=Ne;var f=d.sibling,p=d.return;if(sv(d),d===c){Ne=null;break}if(f!==null){f.return=p,Ne=f;break}Ne=p}}}var g=s.alternate;if(g!==null){var x=g.child;if(x!==null){g.child=null;do{var m=x.sibling;x.sibling=null,x=m}while(x!==null)}}Ne=s}}if(s.subtreeFlags&2064&&o!==null)o.return=s,Ne=o;else e:for(;Ne!==null;){if(s=Ne,s.flags&2048)switch(s.tag){case 0:case 11:case 15:Po(9,s,s.return)}var u=s.sibling;if(u!==null){u.return=s.return,Ne=u;break e}Ne=s.return}}var _=t.current;for(Ne=_;Ne!==null;){o=Ne;var v=o.child;if(o.subtreeFlags&2064&&v!==null)v.return=o,Ne=v;else e:for(o=_;Ne!==null;){if(a=Ne,a.flags&2048)try{switch(a.tag){case 0:case 11:case 15:fc(9,a)}}catch(R){bt(a,a.return,R)}if(a===o){Ne=null;break e}var M=a.sibling;if(M!==null){M.return=a.return,Ne=M;break e}Ne=a.return}}if(ot=r,gr(),ci&&typeof ci.onPostCommitFiberRoot=="function")try{ci.onPostCommitFiberRoot(sc,t)}catch{}i=!0}return i}finally{ht=n,Bn.transition=e}}return!1}function kp(t,e,n){e=Vs(n,e),e=Y_(t,e,1),t=rr(t,e,1),e=sn(),t!==null&&(na(t,1,e),mn(t,e))}function bt(t,e,n){if(t.tag===3)kp(t,t,n);else for(;e!==null;){if(e.tag===3){kp(e,t,n);break}else if(e.tag===1){var i=e.stateNode;if(typeof e.type.getDerivedStateFromError=="function"||typeof i.componentDidCatch=="function"&&(sr===null||!sr.has(i))){t=Vs(n,t),t=q_(e,t,1),e=rr(e,t,1),t=sn(),e!==null&&(na(e,1,t),mn(e,t));break}}e=e.return}}function Ey(t,e,n){var i=t.pingCache;i!==null&&i.delete(e),e=sn(),t.pingedLanes|=t.suspendedLanes&n,Gt===t&&(Xt&n)===n&&(Ft===4||Ft===3&&(Xt&130023424)===Xt&&500>Pt()-df?Ur(t,0):uf|=n),mn(t,e)}function mv(t,e){e===0&&(t.mode&1?(e=xa,xa<<=1,!(xa&130023424)&&(xa=4194304)):e=1);var n=sn();t=Di(t,e),t!==null&&(na(t,e,n),mn(t,n))}function wy(t){var e=t.memoizedState,n=0;e!==null&&(n=e.retryLane),mv(t,n)}function Ty(t,e){var n=0;switch(t.tag){case 13:var i=t.stateNode,r=t.memoizedState;r!==null&&(n=r.retryLane);break;case 19:i=t.stateNode;break;default:throw Error(he(314))}i!==null&&i.delete(e),mv(t,n)}var gv;gv=function(t,e,n){if(t!==null)if(t.memoizedProps!==e.pendingProps||fn.current)hn=!0;else{if(!(t.lanes&n)&&!(e.flags&128))return hn=!1,hy(t,e,n);hn=!!(t.flags&131072)}else hn=!1,Mt&&e.flags&1048576&&y_(e,kl,e.index);switch(e.lanes=0,e.tag){case 2:var i=e.type;hl(t,e),t=e.pendingProps;var r=ks(e,en.current);Ls(e,n),r=rf(null,e,i,t,r,n);var s=sf();return e.flags|=1,typeof r=="object"&&r!==null&&typeof r.render=="function"&&r.$$typeof===void 0?(e.tag=1,e.memoizedState=null,e.updateQueue=null,pn(i)?(s=!0,Ol(e)):s=!1,e.memoizedState=r.state!==null&&r.state!==void 0?r.state:null,Jh(e),r.updater=hc,e.stateNode=r,r._reactInternals=e,Sd(e,i,t,n),e=wd(null,e,i,!0,s,n)):(e.tag=0,Mt&&s&&Wh(e),rn(null,e,r,n),e=e.child),e;case 16:i=e.elementType;e:{switch(hl(t,e),t=e.pendingProps,r=i._init,i=r(i._payload),e.type=i,r=e.tag=Cy(i),t=qn(i,t),r){case 0:e=Ed(null,e,i,t,n);break e;case 1:e=bp(null,e,i,t,n);break e;case 11:e=Ap(null,e,i,t,n);break e;case 14:e=Cp(null,e,i,qn(i.type,t),n);break e}throw Error(he(306,i,""))}return e;case 0:return i=e.type,r=e.pendingProps,r=e.elementType===i?r:qn(i,r),Ed(t,e,i,r,n);case 1:return i=e.type,r=e.pendingProps,r=e.elementType===i?r:qn(i,r),bp(t,e,i,r,n);case 3:e:{if(Q_(e),t===null)throw Error(he(387));i=e.pendingProps,s=e.memoizedState,r=s.element,A_(t,e),Hl(e,i,null,n);var o=e.memoizedState;if(i=o.element,s.isDehydrated)if(s={element:i,isDehydrated:!1,cache:o.cache,pendingSuspenseBoundaries:o.pendingSuspenseBoundaries,transitions:o.transitions},e.updateQueue.baseState=s,e.memoizedState=s,e.flags&256){r=Vs(Error(he(423)),e),e=Rp(t,e,i,n,r);break e}else if(i!==r){r=Vs(Error(he(424)),e),e=Rp(t,e,i,n,r);break e}else for(wn=ir(e.stateNode.containerInfo.firstChild),An=e,Mt=!0,Zn=null,n=w_(e,null,i,n),e.child=n;n;)n.flags=n.flags&-3|4096,n=n.sibling;else{if(Bs(),i===r){e=Ii(t,e,n);break e}rn(t,e,i,n)}e=e.child}return e;case 5:return C_(e),t===null&&vd(e),i=e.type,r=e.pendingProps,s=t!==null?t.memoizedProps:null,o=r.children,fd(i,r)?o=null:s!==null&&fd(i,s)&&(e.flags|=32),J_(t,e),rn(t,e,o,n),e.child;case 6:return t===null&&vd(e),null;case 13:return ev(t,e,n);case 4:return Qh(e,e.stateNode.containerInfo),i=e.pendingProps,t===null?e.child=zs(e,null,i,n):rn(t,e,i,n),e.child;case 11:return i=e.type,r=e.pendingProps,r=e.elementType===i?r:qn(i,r),Ap(t,e,i,r,n);case 7:return rn(t,e,e.pendingProps,n),e.child;case 8:return rn(t,e,e.pendingProps.children,n),e.child;case 12:return rn(t,e,e.pendingProps.children,n),e.child;case 10:e:{if(i=e.type._context,r=e.pendingProps,s=e.memoizedProps,o=r.value,gt(Bl,i._currentValue),i._currentValue=o,s!==null)if(ii(s.value,o)){if(s.children===r.children&&!fn.current){e=Ii(t,e,n);break e}}else for(s=e.child,s!==null&&(s.return=e);s!==null;){var a=s.dependencies;if(a!==null){o=s.child;for(var l=a.firstContext;l!==null;){if(l.context===i){if(s.tag===1){l=Ri(-1,n&-n),l.tag=2;var c=s.updateQueue;if(c!==null){c=c.shared;var d=c.pending;d===null?l.next=l:(l.next=d.next,d.next=l),c.pending=l}}s.lanes|=n,l=s.alternate,l!==null&&(l.lanes|=n),xd(s.return,n,e),a.lanes|=n;break}l=l.next}}else if(s.tag===10)o=s.type===e.type?null:s.child;else if(s.tag===18){if(o=s.return,o===null)throw Error(he(341));o.lanes|=n,a=o.alternate,a!==null&&(a.lanes|=n),xd(o,n,e),o=s.sibling}else o=s.child;if(o!==null)o.return=s;else for(o=s;o!==null;){if(o===e){o=null;break}if(s=o.sibling,s!==null){s.return=o.return,o=s;break}o=o.return}s=o}rn(t,e,r.children,n),e=e.child}return e;case 9:return r=e.type,i=e.pendingProps.children,Ls(e,n),r=zn(r),i=i(r),e.flags|=1,rn(t,e,i,n),e.child;case 14:return i=e.type,r=qn(i,e.pendingProps),r=qn(i.type,r),Cp(t,e,i,r,n);case 15:return K_(t,e,e.type,e.pendingProps,n);case 17:return i=e.type,r=e.pendingProps,r=e.elementType===i?r:qn(i,r),hl(t,e),e.tag=1,pn(i)?(t=!0,Ol(e)):t=!1,Ls(e,n),$_(e,i,r),Sd(e,i,r,n),wd(null,e,i,!0,t,n);case 19:return tv(t,e,n);case 22:return Z_(t,e,n)}throw Error(he(156,e.tag))};function _v(t,e){return jg(t,e)}function Ay(t,e,n,i){this.tag=t,this.key=n,this.sibling=this.child=this.return=this.stateNode=this.type=this.elementType=null,this.index=0,this.ref=null,this.pendingProps=e,this.dependencies=this.memoizedState=this.updateQueue=this.memoizedProps=null,this.mode=i,this.subtreeFlags=this.flags=0,this.deletions=null,this.childLanes=this.lanes=0,this.alternate=null}function kn(t,e,n,i){return new Ay(t,e,n,i)}function mf(t){return t=t.prototype,!(!t||!t.isReactComponent)}function Cy(t){if(typeof t=="function")return mf(t)?1:0;if(t!=null){if(t=t.$$typeof,t===Dh)return 11;if(t===Ih)return 14}return 2}function ar(t,e){var n=t.alternate;return n===null?(n=kn(t.tag,e,t.key,t.mode),n.elementType=t.elementType,n.type=t.type,n.stateNode=t.stateNode,n.alternate=t,t.alternate=n):(n.pendingProps=e,n.type=t.type,n.flags=0,n.subtreeFlags=0,n.deletions=null),n.flags=t.flags&14680064,n.childLanes=t.childLanes,n.lanes=t.lanes,n.child=t.child,n.memoizedProps=t.memoizedProps,n.memoizedState=t.memoizedState,n.updateQueue=t.updateQueue,e=t.dependencies,n.dependencies=e===null?null:{lanes:e.lanes,firstContext:e.firstContext},n.sibling=t.sibling,n.index=t.index,n.ref=t.ref,n}function ml(t,e,n,i,r,s){var o=2;if(i=t,typeof t=="function")mf(t)&&(o=1);else if(typeof t=="string")o=5;else e:switch(t){case ps:return Or(n.children,r,s,e);case Nh:o=8,r|=8;break;case Wu:return t=kn(12,n,e,r|2),t.elementType=Wu,t.lanes=s,t;case Xu:return t=kn(13,n,e,r),t.elementType=Xu,t.lanes=s,t;case $u:return t=kn(19,n,e,r),t.elementType=$u,t.lanes=s,t;case Cg:return mc(n,r,s,e);default:if(typeof t=="object"&&t!==null)switch(t.$$typeof){case Tg:o=10;break e;case Ag:o=9;break e;case Dh:o=11;break e;case Ih:o=14;break e;case Xi:o=16,i=null;break e}throw Error(he(130,t==null?t:typeof t,""))}return e=kn(o,n,e,r),e.elementType=t,e.type=i,e.lanes=s,e}function Or(t,e,n,i){return t=kn(7,t,i,e),t.lanes=n,t}function mc(t,e,n,i){return t=kn(22,t,i,e),t.elementType=Cg,t.lanes=n,t.stateNode={isHidden:!1},t}function Kc(t,e,n){return t=kn(6,t,null,e),t.lanes=n,t}function Zc(t,e,n){return e=kn(4,t.children!==null?t.children:[],t.key,e),e.lanes=n,e.stateNode={containerInfo:t.containerInfo,pendingChildren:null,implementation:t.implementation},e}function by(t,e,n,i,r){this.tag=e,this.containerInfo=t,this.finishedWork=this.pingCache=this.current=this.pendingChildren=null,this.timeoutHandle=-1,this.callbackNode=this.pendingContext=this.context=null,this.callbackPriority=0,this.eventTimes=Lc(0),this.expirationTimes=Lc(-1),this.entangledLanes=this.finishedLanes=this.mutableReadLanes=this.expiredLanes=this.pingedLanes=this.suspendedLanes=this.pendingLanes=0,this.entanglements=Lc(0),this.identifierPrefix=i,this.onRecoverableError=r,this.mutableSourceEagerHydrationData=null}function gf(t,e,n,i,r,s,o,a,l){return t=new by(t,e,n,a,l),e===1?(e=1,s===!0&&(e|=8)):e=0,s=kn(3,null,null,e),t.current=s,s.stateNode=t,s.memoizedState={element:i,isDehydrated:n,cache:null,transitions:null,pendingSuspenseBoundaries:null},Jh(s),t}function Ry(t,e,n){var i=3<arguments.length&&arguments[3]!==void 0?arguments[3]:null;return{$$typeof:fs,key:i==null?null:""+i,children:t,containerInfo:e,implementation:n}}function vv(t){if(!t)return dr;t=t._reactInternals;e:{if(Xr(t)!==t||t.tag!==1)throw Error(he(170));var e=t;do{switch(e.tag){case 3:e=e.stateNode.context;break e;case 1:if(pn(e.type)){e=e.stateNode.__reactInternalMemoizedMergedChildContext;break e}}e=e.return}while(e!==null);throw Error(he(171))}if(t.tag===1){var n=t.type;if(pn(n))return v_(t,n,e)}return e}function xv(t,e,n,i,r,s,o,a,l){return t=gf(n,i,!0,t,r,s,o,a,l),t.context=vv(null),n=t.current,i=sn(),r=or(n),s=Ri(i,r),s.callback=e??null,rr(n,s,r),t.current.lanes=r,na(t,r,i),mn(t,i),t}function gc(t,e,n,i){var r=e.current,s=sn(),o=or(r);return n=vv(n),e.context===null?e.context=n:e.pendingContext=n,e=Ri(s,o),e.payload={element:t},i=i===void 0?null:i,i!==null&&(e.callback=i),t=rr(r,e,o),t!==null&&(ti(t,r,o,s),cl(t,r,o)),o}function ql(t){if(t=t.current,!t.child)return null;switch(t.child.tag){case 5:return t.child.stateNode;default:return t.child.stateNode}}function Bp(t,e){if(t=t.memoizedState,t!==null&&t.dehydrated!==null){var n=t.retryLane;t.retryLane=n!==0&&n<e?n:e}}function _f(t,e){Bp(t,e),(t=t.alternate)&&Bp(t,e)}function Py(){return null}var yv=typeof reportError=="function"?reportError:function(t){console.error(t)};function vf(t){this._internalRoot=t}_c.prototype.render=vf.prototype.render=function(t){var e=this._internalRoot;if(e===null)throw Error(he(409));gc(t,e,null,null)};_c.prototype.unmount=vf.prototype.unmount=function(){var t=this._internalRoot;if(t!==null){this._internalRoot=null;var e=t.containerInfo;Hr(function(){gc(null,t,null,null)}),e[Ni]=null}};function _c(t){this._internalRoot=t}_c.prototype.unstable_scheduleHydration=function(t){if(t){var e=Zg();t={blockedOn:null,target:t,priority:e};for(var n=0;n<qi.length&&e!==0&&e<qi[n].priority;n++);qi.splice(n,0,t),n===0&&Qg(t)}};function xf(t){return!(!t||t.nodeType!==1&&t.nodeType!==9&&t.nodeType!==11)}function vc(t){return!(!t||t.nodeType!==1&&t.nodeType!==9&&t.nodeType!==11&&(t.nodeType!==8||t.nodeValue!==" react-mount-point-unstable "))}function zp(){}function Ly(t,e,n,i,r){if(r){if(typeof i=="function"){var s=i;i=function(){var c=ql(o);s.call(c)}}var o=xv(e,i,t,0,null,!1,!1,"",zp);return t._reactRootContainer=o,t[Ni]=o.current,jo(t.nodeType===8?t.parentNode:t),Hr(),o}for(;r=t.lastChild;)t.removeChild(r);if(typeof i=="function"){var a=i;i=function(){var c=ql(l);a.call(c)}}var l=gf(t,0,!1,null,null,!1,!1,"",zp);return t._reactRootContainer=l,t[Ni]=l.current,jo(t.nodeType===8?t.parentNode:t),Hr(function(){gc(e,l,n,i)}),l}function xc(t,e,n,i,r){var s=n._reactRootContainer;if(s){var o=s;if(typeof r=="function"){var a=r;r=function(){var l=ql(o);a.call(l)}}gc(e,o,t,r)}else o=Ly(n,e,t,r,i);return ql(o)}qg=function(t){switch(t.tag){case 3:var e=t.stateNode;if(e.current.memoizedState.isDehydrated){var n=yo(e.pendingLanes);n!==0&&(Fh(e,n|1),mn(e,Pt()),!(ot&6)&&(Gs=Pt()+500,gr()))}break;case 13:Hr(function(){var i=Di(t,1);if(i!==null){var r=sn();ti(i,t,1,r)}}),_f(t,1)}};kh=function(t){if(t.tag===13){var e=Di(t,134217728);if(e!==null){var n=sn();ti(e,t,134217728,n)}_f(t,134217728)}};Kg=function(t){if(t.tag===13){var e=or(t),n=Di(t,e);if(n!==null){var i=sn();ti(n,t,e,i)}_f(t,e)}};Zg=function(){return ht};Jg=function(t,e){var n=ht;try{return ht=t,e()}finally{ht=n}};id=function(t,e,n){switch(e){case"input":if(Ku(t,n),e=n.name,n.type==="radio"&&e!=null){for(n=t;n.parentNode;)n=n.parentNode;for(n=n.querySelectorAll("input[name="+JSON.stringify(""+e)+'][type="radio"]'),e=0;e<n.length;e++){var i=n[e];if(i!==t&&i.form===t.form){var r=cc(i);if(!r)throw Error(he(90));Rg(i),Ku(i,r)}}}break;case"textarea":Lg(t,n);break;case"select":e=n.value,e!=null&&Cs(t,!!n.multiple,e,!1)}};kg=hf;Bg=Hr;var Ny={usingClientEntryPoint:!1,Events:[ra,vs,cc,Og,Fg,hf]},uo={findFiberByHostInstance:Pr,bundleType:0,version:"18.3.1",rendererPackageName:"react-dom"},Dy={bundleType:uo.bundleType,version:uo.version,rendererPackageName:uo.rendererPackageName,rendererConfig:uo.rendererConfig,overrideHookState:null,overrideHookStateDeletePath:null,overrideHookStateRenamePath:null,overrideProps:null,overridePropsDeletePath:null,overridePropsRenamePath:null,setErrorHandler:null,setSuspenseHandler:null,scheduleUpdate:null,currentDispatcherRef:Oi.ReactCurrentDispatcher,findHostInstanceByFiber:function(t){return t=Vg(t),t===null?null:t.stateNode},findFiberByHostInstance:uo.findFiberByHostInstance||Py,findHostInstancesForRefresh:null,scheduleRefresh:null,scheduleRoot:null,setRefreshHandler:null,getCurrentFiber:null,reconcilerVersion:"18.3.1-next-f1338f8080-20240426"};if(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__<"u"){var Pa=__REACT_DEVTOOLS_GLOBAL_HOOK__;if(!Pa.isDisabled&&Pa.supportsFiber)try{sc=Pa.inject(Dy),ci=Pa}catch{}}Rn.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED=Ny;Rn.createPortal=function(t,e){var n=2<arguments.length&&arguments[2]!==void 0?arguments[2]:null;if(!xf(e))throw Error(he(200));return Ry(t,e,null,n)};Rn.createRoot=function(t,e){if(!xf(t))throw Error(he(299));var n=!1,i="",r=yv;return e!=null&&(e.unstable_strictMode===!0&&(n=!0),e.identifierPrefix!==void 0&&(i=e.identifierPrefix),e.onRecoverableError!==void 0&&(r=e.onRecoverableError)),e=gf(t,1,!1,null,null,n,!1,i,r),t[Ni]=e.current,jo(t.nodeType===8?t.parentNode:t),new vf(e)};Rn.findDOMNode=function(t){if(t==null)return null;if(t.nodeType===1)return t;var e=t._reactInternals;if(e===void 0)throw typeof t.render=="function"?Error(he(188)):(t=Object.keys(t).join(","),Error(he(268,t)));return t=Vg(e),t=t===null?null:t.stateNode,t};Rn.flushSync=function(t){return Hr(t)};Rn.hydrate=function(t,e,n){if(!vc(e))throw Error(he(200));return xc(null,t,e,!0,n)};Rn.hydrateRoot=function(t,e,n){if(!xf(t))throw Error(he(405));var i=n!=null&&n.hydratedSources||null,r=!1,s="",o=yv;if(n!=null&&(n.unstable_strictMode===!0&&(r=!0),n.identifierPrefix!==void 0&&(s=n.identifierPrefix),n.onRecoverableError!==void 0&&(o=n.onRecoverableError)),e=xv(e,null,t,1,n??null,r,!1,s,o),t[Ni]=e.current,jo(t),i)for(t=0;t<i.length;t++)n=i[t],r=n._getVersion,r=r(n._source),e.mutableSourceEagerHydrationData==null?e.mutableSourceEagerHydrationData=[n,r]:e.mutableSourceEagerHydrationData.push(n,r);return new _c(e)};Rn.render=function(t,e,n){if(!vc(e))throw Error(he(200));return xc(null,t,e,!1,n)};Rn.unmountComponentAtNode=function(t){if(!vc(t))throw Error(he(40));return t._reactRootContainer?(Hr(function(){xc(null,null,t,!1,function(){t._reactRootContainer=null,t[Ni]=null})}),!0):!1};Rn.unstable_batchedUpdates=hf;Rn.unstable_renderSubtreeIntoContainer=function(t,e,n,i){if(!vc(n))throw Error(he(200));if(t==null||t._reactInternals===void 0)throw Error(he(38));return xc(t,e,n,!1,i)};Rn.version="18.3.1-next-f1338f8080-20240426";function Sv(){if(!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__>"u"||typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE!="function"))try{__REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(Sv)}catch(t){console.error(t)}}Sv(),Sg.exports=Rn;var Iy=Sg.exports,Mv,Hp=Iy;Mv=Hp.createRoot,Hp.hydrateRoot;async function mi(t,e){const n=await fetch(t,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(e)}),i=await n.json().catch(()=>({}));if(!n.ok)throw new Error(i.detail||`${n.status} ${n.statusText}`);return i}const St={parse:t=>mi("/api/parse",{csv:t}),build:(t,e)=>mi("/api/build",e?{...t,options:e}:t),reverse:(t,e={})=>mi("/api/reverse",{xyz:t,...e}),reverseBackends:()=>fetch("/api/reverse/backends").then(t=>t.json()),represent:(t,e,n)=>mi("/api/reverse/represent",{xyz:t,key:e,overall_charge:n}),reverseExport:(t,e)=>mi("/api/reverse/export",{items:t,columns:e}),isomers:t=>mi("/api/isomers",t),perceive:t=>mi("/api/perceive",t),submitJob:(t,e,n,i)=>mi("/api/jobs",{complexes:t,relax:e,xtb_timeout_s:n,options:i}),getJob:async t=>(await fetch(`/api/jobs/${t}`)).json(),cancelJob:t=>mi(`/api/jobs/${t}/cancel`,{}),geometries:()=>fetch("/api/geometries").then(t=>t.json()),version:()=>fetch("/api/version").then(t=>t.json()),stats:()=>fetch("/api/stats").then(t=>{if(!t.ok)throw new Error(`${t.status} ${t.statusText}`);return t.json()}),depict:t=>fetch(`/api/depict?smiles=${encodeURIComponent(t)}`).then(e=>e.json()),depictSvg:t=>fetch(`/api/depict_svg?smiles=${encodeURIComponent(t)}`).then(e=>e.json()),vertices:(t,e)=>fetch(`/api/vertices?geometry=${encodeURIComponent(t)}&denticities=${e.join(",")}`).then(n=>n.json()),sites:(t,e,n=[],i=[])=>fetch(`/api/sites?geometry=${encodeURIComponent(t)}&denticities=${e.join(",")}`+(n.length?`&arene=${n.join(",")}`:"")+(i.length?`&cap=${i.join(",")}`:"")).then(r=>r.json()),fileUrl:t=>`/api/file/${t}`,fileUrlAs:(t,e)=>`/api/file/${t.replace(/\.[^./]+$/,"."+e)}`,fileText:t=>fetch(`/api/file/${t}`).then(e=>e.text()),downloadAllUrl:t=>`/api/download/${t}`},Uy=""+new URL("freilab-logo-B1ySkVI-.png",import.meta.url).href,Oy=""+new URL("freilab-logo-dark-C3ZYKBwr.svg",import.meta.url).href,Vp=""+new URL("mecobi-logo-BTECWjwi.svg",import.meta.url).href;function Qo({busy:t,label:e,busyLabel:n,compact:i=!1}){return y.jsxs("span",{className:"busy-label",children:[y.jsx("span",{className:t?"busy-hide":void 0,children:e}),y.jsxs("span",{className:t?void 0:"busy-hide",children:[y.jsx("span",{className:"spinner","aria-hidden":"true"}),i?y.jsx("span",{className:"sr-only",children:n}):n]})]})}const Fy=.2,ky=5,Gp=1.25,Jc=t=>Math.min(ky,Math.max(Fy,t));function By({atoms:t,bonds:e,selected:n,onToggle:i}){const[r,s]=Q.useState(1),o=Q.useRef(null),[a,l]=Q.useState(0),c=Q.useRef([]),d=Q.useRef(!1),h=!!(t!=null&&t.length),f=h?t.map(U=>U.x):[0],p=h?t.map(U=>U.y):[0],g=Math.min(...f),x=Math.max(...f),m=Math.min(...p),u=Math.max(...p),_=1.1,v=30,M=(x-g+2*_)*v,R=(u-m+2*_)*v,C=U=>(U-g+_)*v,A=U=>(u-U+_)*v,P=Q.useCallback(()=>{const U=o.current;if(!U||!M||!R)return 1;const Y=U.clientWidth-4,V=U.clientHeight-4;return Jc(Math.min(Y/M,V/R,1))},[M,R]);if(Q.useLayoutEffect(()=>{d.current=!1,s(P())},[P]),Q.useLayoutEffect(()=>{const U=o.current;if(!U||typeof ResizeObserver>"u")return;const Y=new ResizeObserver(()=>{d.current||s(P())});return Y.observe(U),()=>Y.disconnect()},[P]),Q.useLayoutEffect(()=>{const U=o.current;if(!U)return;const Y=V=>{V.ctrlKey&&(V.preventDefault(),d.current=!0,s(J=>Jc(J*Math.exp(-V.deltaY*.0015))))};return U.addEventListener("wheel",Y,{passive:!1}),()=>U.removeEventListener("wheel",Y)},[]),!h)return null;const E=U=>{d.current=!0,s(Y=>Jc(Y*U))},S=new Set(n||[]),D=Math.min(a,t.length-1),X=U=>{var V;const Y=Math.max(0,Math.min(t.length-1,U));l(Y),(V=c.current[Y])==null||V.focus()},H=(U,Y)=>{const V={ArrowRight:Y+1,ArrowDown:Y+1,ArrowLeft:Y-1,ArrowUp:Y-1,Home:0,End:t.length-1};U.key in V?(U.preventDefault(),X(V[U.key])):(U.key===" "||U.key==="Enter")&&(U.preventDefault(),i(t[Y].idx))};return y.jsxs("div",{className:"depiction",children:[y.jsxs("div",{className:"depiction-controls",children:[y.jsx("button",{type:"button",className:"ghost",title:"Zoom out",onClick:()=>E(1/Gp),children:"−"}),y.jsxs("button",{type:"button",className:"ghost",title:"Fit to area",onClick:()=>{d.current=!1,s(P())},children:[Math.round(r*100),"%"]}),y.jsx("button",{type:"button",className:"ghost",title:"Zoom in",onClick:()=>E(Gp),children:"+"}),y.jsx("span",{className:"muted depiction-hint",children:"Ctrl + scroll to zoom"})]}),y.jsx("div",{className:"depiction-viewport",ref:o,children:y.jsxs("svg",{width:M*r,height:R*r,viewBox:`0 0 ${M} ${R}`,style:{display:"block"},role:"group","aria-label":"Donor atoms. Arrow keys move between atoms, Space marks or unmarks a donor.",children:[e.map((U,Y)=>{const V=t[U.a],J=t[U.b];return y.jsx("line",{x1:C(V.x),y1:A(V.y),x2:C(J.x),y2:A(J.y),stroke:"var(--text-secondary)",strokeWidth:U.order>=2?3:1.5},Y)}),t.map((U,Y)=>{const V=S.has(U.idx);return y.jsxs("g",{ref:J=>{c.current[Y]=J},className:"depiction-atom",role:"checkbox","aria-checked":V,"aria-label":`${U.symbol}, atom ${U.idx}`,tabIndex:Y===D?0:-1,onFocus:()=>l(Y),onKeyDown:J=>H(J,Y),onClick:()=>i(U.idx),style:{cursor:"pointer"},children:[y.jsx("circle",{cx:C(U.x),cy:A(U.y),r:V?12:9.5,fill:V?"var(--accent-500)":"var(--surface-1)",stroke:V?"var(--accent-bright)":"var(--border-strong)",strokeWidth:1.5}),y.jsx("text",{x:C(U.x),y:A(U.y),textAnchor:"middle",dominantBaseline:"central",fontSize:"10.5",fontFamily:"var(--mono)",fill:V?"var(--on-accent)":"var(--text-primary)",children:U.symbol})]},U.idx)})]})})]})}function zy(t,e){var o,a;if(!t||e.length!==5&&e.length!==6)return!1;const n=new Set(e),i={};for(const l of t.atoms)i[l.idx]=l;if(![...n].every(l=>{var c;return((c=i[l])==null?void 0:c.symbol)==="C"}))return!1;const r={};let s=0;for(const l of t.bonds||[]){const c=(o=t.atoms[l.a])==null?void 0:o.idx,d=(a=t.atoms[l.b])==null?void 0:a.idx;n.has(c)&&n.has(d)&&(r[c]=(r[c]||0)+1,r[d]=(r[d]||0)+1,s++)}return s===e.length&&[...n].every(l=>r[l]===2)}function Hy({ligand:t,onChange:e,onApplyToAll:n}){var c;const[i,r]=Q.useState(null),[s,o]=Q.useState("");Q.useEffect(()=>{let d=!1;return r(null),o(""),St.depict(t.smiles).then(h=>{d||(h.detail?o(h.detail):r(h))}).catch(h=>!d&&o(String(h))),()=>{d=!0}},[t.smiles]);const a=t.coord_atoms||[],l=d=>{const h=a.includes(d)?a.filter(f=>f!==d):[...a,d].sort((f,p)=>f-p);e(h,zy(i,h))};return y.jsxs("div",{style:{display:"flex",flexDirection:"column",gap:6,padding:"4px 0"},children:[y.jsxs("div",{children:[y.jsx("div",{className:"mono",style:{fontSize:"var(--text-caption)",marginBottom:4,wordBreak:"break-all"},children:t.smiles}),y.jsxs("div",{className:"muted",style:{fontSize:"var(--text-caption)"},children:["donors: ",y.jsxs("span",{className:"mono",children:["[",a.join(", "),"]"]}),t.is_arene?y.jsxs("span",{className:"chip",style:{marginLeft:6},title:"η-cap (occupies 3 coordination sites)",children:["η",((c=t.coord_atoms)==null?void 0:c.length)??""]}):null]}),n?y.jsx("button",{className:"ghost",style:{marginTop:6,fontSize:"var(--text-caption)"},disabled:!a.length,title:"Set these donor atoms on every complex that uses this same ligand",onClick:()=>n(t.smiles,a),children:"Apply to all matching"}):null]}),s?y.jsx("span",{className:"pill-err",children:s}):i?y.jsx(By,{atoms:i.atoms,bonds:i.bonds,selected:a,onToggle:l}):y.jsx("span",{className:"spinner"})]})}function Vy({ligands:t,onChange:e,onApplyToAll:n,onSave:i,onCancel:r}){return y.jsxs("div",{className:"donor-panel",children:[y.jsxs("div",{className:"donor-panel-head",children:[y.jsx("div",{className:"muted",children:"Click atoms to set the coordinating (donor) atoms for each ligand:"}),(i||r)&&y.jsxs("div",{className:"donor-panel-actions",children:[i&&y.jsx("button",{className:"icon-btn save",title:"Save this selection","aria-label":"Save selection",onClick:i,children:y.jsx("svg",{viewBox:"0 0 20 20",width:"15",height:"15","aria-hidden":"true",children:y.jsx("path",{d:"M4 10.5 L8 14.5 L16 5.5",fill:"none",stroke:"currentColor",strokeWidth:"2.2",strokeLinecap:"round",strokeLinejoin:"round"})})}),r&&y.jsx("button",{className:"icon-btn",title:"Cancel (discard changes)","aria-label":"Cancel",onClick:r,children:y.jsx("svg",{viewBox:"0 0 20 20",width:"15",height:"15","aria-hidden":"true",children:y.jsx("path",{d:"M5 5 L15 15 M15 5 L5 15",fill:"none",stroke:"currentColor",strokeWidth:"2.2",strokeLinecap:"round"})})})]})]}),y.jsx("div",{className:"donor-grid",children:t.map((s,o)=>y.jsx(Hy,{ligand:s,onChange:a=>e(o,a),onApplyToAll:n},o))})]})}function Gy({cx:t,sel:e,index:n,onRowChange:i,children:r}){const[s,o]=Q.useState({summary:null,stereoSplits:!1}),a=Q.useRef(null),[l,c]=Q.useState(!1),d=JSON.stringify({ligands:e.ligands,geometry:e.geometry,stereo:e.stereo});return Q.useEffect(()=>{if(l)return;const h=a.current;if(!h)return;if(typeof IntersectionObserver>"u"){c(!0);return}const f=new IntersectionObserver(p=>{p.some(g=>g.isIntersecting)&&(c(!0),f.disconnect())},{rootMargin:"200px"});return f.observe(h),()=>f.disconnect()},[l]),Q.useEffect(()=>{if(!l||!t.supported||!e.geometry){o({summary:null,stereoSplits:!1});return}let h=!1;return St.isomers({metal:t.metal,oxidation_state:t.oxidation_state,ligands:e.ligands,geometry:e.geometry,stereo:e.stereo}).then(f=>!h&&o({summary:f.summary||null,stereoSplits:!!f.stereo_splits})).catch(()=>!h&&o({summary:null,stereoSplits:!1})),()=>{h=!0}},[d,t.supported,l]),y.jsxs("div",{ref:a,className:"isomer-cell",children:[y.jsxs("div",{className:"iso-row",children:[y.jsxs("div",{className:"iso-toggles",children:[y.jsxs("div",{className:"iso-checks",children:[y.jsxs("label",{className:"switch",children:[y.jsx("input",{type:"checkbox",checked:e.allIsomers,onChange:h=>i(n,{allIsomers:h.target.checked})}),"all"]}),e.allIsomers&&s.stereoSplits&&y.jsxs("label",{className:"switch",title:"Split Δ/Λ enantiomers and asymmetric-chelate donor directions",children:[y.jsx("input",{type:"checkbox",checked:e.stereo,onChange:h=>i(n,{stereo:h.target.checked})}),"Δ/Λ"]})]}),s.summary&&y.jsx("div",{className:"iso-hint muted",title:"Distinct isomers 'all' will build",children:s.summary})]}),r]}),e.siteAssignment&&y.jsxs("span",{className:"chip custom-isomer","data-tour":n===0?"custom-isomer-flag":void 0,title:"A custom isomer was set in the isomer editor. Build and Build all use it.",children:["★ custom",y.jsx("button",{type:"button",className:"chip-x",title:"Clear the custom isomer",onClick:()=>i(n,{siteAssignment:null}),children:"×"})]})]})}function jy(t,e){return t==="octahedral"&&e?"piano-stool":t.replace("_"," ")}function Wy({rows:t,onRowChange:e,onDonorsChange:n,onApplyDonorsToAll:i,onBuild:r,onRemoveRow:s,onRemoveAllRows:o,onAssign:a,buildingIndex:l,building:c,onBuildAll:d,jobStatus:h,timerText:f,jobRunning:p,jobProgress:g,canCancel:x,onCancelJob:m,onDismissJob:u,relax:_,setRelax:v,spin:M,setSpin:R,maxOptTime:C,setMaxOptTime:A,advOptions:P,setAdvOptions:E,optionGroups:S,advDefaults:D}){const[X,H]=Q.useState(!1),U=p||c,Y=Q.useRef(null),[V,J]=Q.useState({left:!1,right:!1});return Q.useEffect(()=>{const N=Y.current;if(!N||typeof ResizeObserver>"u")return;const j=()=>{const fe=N.scrollLeft>1,_e=N.scrollLeft+N.clientWidth<N.scrollWidth-1;J(Re=>Re.left===fe&&Re.right===_e?Re:{left:fe,right:_e})},Z=new ResizeObserver(j);return Z.observe(N),N.firstElementChild&&Z.observe(N.firstElementChild),N.addEventListener("scroll",j,{passive:!0}),j(),()=>{Z.disconnect(),N.removeEventListener("scroll",j)}},[t.length]),y.jsxs("div",{className:"card",children:[y.jsxs("div",{className:"row",style:{justifyContent:"space-between",marginBottom:12},children:[y.jsx("h2",{style:{margin:0},children:"Review & build"}),y.jsx("button",{className:"primary","data-tour":"build-all-btn",onClick:d,disabled:U,title:U?"A build is already running — wait for it or cancel it first":void 0,children:"Build all (queue job)"})]}),y.jsxs("div",{className:"build-controls","data-tour":"build-controls",children:[y.jsxs("div",{className:"xtb-bar",children:[y.jsxs("span",{className:"switch",children:[y.jsx("input",{type:"checkbox",id:"relax",checked:_,onChange:N=>v(N.target.checked)}),y.jsx("label",{htmlFor:"relax",children:"Relax with xtb (GFN2)"})]}),y.jsxs("span",{className:"xtb-controls"+(_?"":" disabled"),children:[y.jsx("label",{htmlFor:"spin",children:"Spin"}),y.jsxs("select",{id:"spin",value:M,disabled:!_,onChange:N=>R(N.target.value),children:[y.jsx("option",{value:"low",children:"low"}),y.jsx("option",{value:"high",children:"high"})]}),y.jsx("label",{htmlFor:"maxopt",title:"Max wall-clock time for each structure's xtb optimisation",children:"Max opt time"}),y.jsx("input",{type:"range",id:"maxopt",min:30,max:600,step:30,value:C,disabled:!_,onChange:N=>A(Number(N.target.value))}),y.jsxs("span",{className:"mono",style:{minWidth:42},children:[C,"s"]})]}),S&&y.jsxs("button",{type:"button",className:"adv-toggle","aria-expanded":X,onClick:()=>H(N=>!N),children:[y.jsx("span",{className:"adv-caret","aria-hidden":"true",children:X?"▾":"▸"}),"Advanced options",(()=>{const N=D?Object.keys(P).filter(j=>P[j]!==D[j]).length:0;return N?y.jsxs("span",{className:"pill-warn",style:{marginLeft:6},children:[N," changed"]}):null})()]})]}),S&&X&&y.jsxs("div",{className:"adv-body",children:[y.jsxs("div",{className:"adv-head",children:[y.jsxs("p",{className:"hint",children:["Fine-tune how a structure is built — geometry prep before optimisation, and xtb constraints during it. The defaults are the standard build; only change these to diagnose a specific complex. Options marked ",y.jsx("strong",{children:"⚑ opt-in"})," ","are off by default (escalations for a hard, crowded sphere) and can cost accuracy elsewhere, so leave them off unless a build actually needs them."]}),D&&y.jsx("button",{type:"button",className:"adv-reset",onClick:()=>E({...D}),children:"Reset to defaults"})]}),S.map(N=>y.jsxs("div",{className:"adv-group",children:[y.jsx("div",{className:"adv-group-label",children:N.label}),y.jsx("div",{className:"adv-grid",children:N.items.map(([j,Z,fe])=>{const _e=D&&D[j]===!1;return y.jsxs("label",{className:"adv-item",children:[y.jsx("input",{type:"checkbox",checked:!!P[j],onChange:Re=>E({...P,[j]:Re.target.checked})}),y.jsxs("span",{className:"adv-label",children:[y.jsx("span",{className:"adv-label-text",children:Z}),_e?y.jsx("span",{className:"adv-optin",title:"Off by default — an opt-in escalation for hard, crowded spheres",children:"⚑ opt-in"}):null]}),y.jsx("span",{className:"adv-tip",role:"tooltip",children:fe})]},j)})})]},N.label))]})]}),h||p||c?y.jsxs("div",{style:{marginBottom:10},children:[y.jsxs("div",{className:"row",style:{alignItems:"flex-start",gap:8},children:[y.jsx("div",{style:{flex:1,minWidth:0},children:h||y.jsxs("div",{className:"job-line",children:[y.jsx("span",{className:"spinner"}),y.jsx("span",{className:"job-title",children:c?"Building…":"Submitting…"})]})}),f?y.jsx("span",{className:"build-timer mono",title:"Build time",children:f}):null,x&&m?y.jsx("button",{className:"toggle-btn",title:"Cancel this job (a queued job stops immediately; a running one stops after the current structure finishes)",onClick:m,children:"Cancel"}):null,!p&&h&&u?y.jsx("button",{className:"toggle-btn",title:"Dismiss (also clears the #job link)",onClick:u,children:"Dismiss"}):null]}),c||p?g>0?y.jsx("div",{className:"progress",style:{marginTop:8},title:`${Math.round(g*100)}%`,role:"progressbar","aria-label":"Build progress","aria-valuemin":0,"aria-valuemax":100,"aria-valuenow":Math.round(g*100),children:y.jsx("div",{className:"progress-fill",style:{width:`${Math.round(g*100)}%`}})}):y.jsx("div",{className:"progress indeterminate",style:{marginTop:8},role:"progressbar","aria-label":"Build progress",children:y.jsx("div",{className:"progress-fill"})}):null]}):null,!h&&!p&&!c&&f?y.jsx("div",{style:{marginBottom:10},children:y.jsx("span",{className:"build-timer mono",children:f})}):null,y.jsx("div",{className:"table-scroll-wrap"+(V.left?" can-left":"")+(V.right?" can-right":""),children:y.jsx("div",{className:"table-scroll",ref:Y,"data-tour":"complex-table",children:y.jsxs("table",{children:[y.jsx("thead",{children:y.jsxs("tr",{children:[y.jsx("th",{className:"remove-col","aria-label":"Remove",children:o?y.jsxs("button",{type:"button",className:"ghost row-remove-all-btn",title:"Remove all complexes from the list","aria-label":"Remove all complexes",onClick:o,children:["Remove",y.jsx("br",{}),"all"]}):null}),y.jsx("th",{children:"Name"}),y.jsx("th",{children:"Metal"}),y.jsx("th",{children:"CN"}),y.jsx("th",{children:"Charge"}),y.jsx("th",{children:"Ligands (denticity)"}),y.jsx("th",{children:"Geometry"}),y.jsx("th",{style:{whiteSpace:"nowrap"},"data-tour":"donors-col",title:"Untick to edit the donor atoms",children:"Donors"}),y.jsx("th",{children:"Isomers"}),y.jsx("th",{className:"act-col",children:y.jsx("span",{className:"sr-only",children:"Build"})})]})}),y.jsx("tbody",{children:t.map((N,j)=>{var _e;const Z=N.sel,fe=(_e=Z.ligands)==null?void 0:_e.some(Re=>Re.is_arene);return y.jsxs(Q.Fragment,{children:[y.jsxs("tr",{className:N.warning?"row-warn":"",children:[y.jsx("td",{className:"remove-col",children:s?y.jsx("button",{type:"button",className:"ghost row-remove-btn",title:"Remove this complex from the list","aria-label":`Remove ${N.name||"complex"}`,onClick:()=>s(j),children:y.jsx("svg",{width:"10",height:"10",viewBox:"0 0 10 10","aria-hidden":"true",children:y.jsx("path",{d:"M1 1L9 9M9 1L1 9",stroke:"currentColor",strokeWidth:"1.6",strokeLinecap:"round"})})}):null}),y.jsx("td",{className:"mono",children:N.name??"—"}),y.jsxs("td",{className:"mono",children:[N.metal,"(",N.oxidation_state??"?",")",N.warning?y.jsx("span",{className:"warn-mark",title:N.warning,children:"⚠"}):null]}),y.jsx("td",{children:N.coordination_number??"—"}),y.jsx("td",{className:"mono",children:N.total_charge}),y.jsx("td",{children:N.ligands.map((Re,I)=>{var z,ie;return y.jsxs("span",{className:"chip lig-chip"+(Re.warning?" chip-warn":""),title:Re.warning||Re.smiles,children:[y.jsx("span",{className:"chip-smiles",children:Re.smiles}),y.jsx("span",{className:"chip-dent",title:Re.is_arene?`η${((z=Re.coord_atoms)==null?void 0:z.length)??"?"} cap (occupies 3 coordination sites)`:`denticity ${Re.denticity??"?"}`,children:Re.is_arene?`η${((ie=Re.coord_atoms)==null?void 0:ie.length)??"?"}`:Re.denticity??"?"}),Re.warning?y.jsx("span",{className:"chip-warn-mark",children:"⚠"}):null]},I)})}),y.jsx("td",{children:N.supported?y.jsxs(y.Fragment,{children:[y.jsx("select",{"aria-label":`Geometry for ${N.name}`,value:Z.geometry,onChange:Re=>e(j,{geometry:Re.target.value}),children:N.geometry_options.map(Re=>y.jsx("option",{value:Re,children:jy(Re,fe)},Re))}),N.needs_cap_selection?y.jsx("div",{className:"pill-warn",style:{marginTop:4,fontSize:"var(--text-caption)"},title:"Looks like a metallocene/sandwich. Untick Donors and select each Cp/arene ring so it counts as one η-cap — otherwise the batch build skips this row.",children:"⚠ select ring(s) as η-caps · skipped by Build all"}):null]}):y.jsx("span",{className:"pill-err",children:N.error||"unsupported"})}),y.jsx("td",{children:y.jsx("input",{type:"checkbox","aria-label":`Donor atoms correct for ${N.name}`,title:"Untick to edit the donor atoms","data-tour":j===1?"ferroquine-donors":void 0,checked:Z.donorsCorrect,onChange:Re=>e(j,Re.target.checked?{donorsCorrect:!0}:{donorsCorrect:!1,donorsSnapshot:Z.ligands})})}),y.jsx("td",{children:y.jsx(Gy,{cx:N,sel:Z,index:j,onRowChange:e,children:(()=>{const Re=(Z.geometry||"").startsWith("metallocene");return y.jsx("button",{className:"ghost iso-editor-btn","data-tour":j===0?"assign-btn":void 0,disabled:!N.supported||Re,onClick:()=>a(j),"aria-label":`Isomer editor for ${N.name}`,title:Re?"The isomer editor isn't available for metallocenes":"Define a specific isomer in 3D",children:"Isomer editor"})})()})}),y.jsx("td",{className:"act-col",children:y.jsx("button",{className:"primary",disabled:!N.supported||U,onClick:()=>r(j),title:U?"A build is already running — wait for it or cancel it first":void 0,children:y.jsx(Qo,{busy:l===j,label:"Build",busyLabel:"Building…",compact:!0})})})]}),!Z.donorsCorrect&&y.jsx("tr",{children:y.jsx("td",{colSpan:10,style:{paddingTop:0},"data-tour":j===1?"donor-panel":void 0,children:y.jsx(Vy,{ligands:Z.ligands,onChange:(Re,I,z)=>{const ie=Z.ligands.map((le,ye)=>ye===Re?{...le,coord_atoms:I,is_arene:z}:le);n(j,ie)},onApplyToAll:i,onSave:()=>e(j,{donorsCorrect:!0}),onCancel:()=>{Z.donorsSnapshot&&n(j,Z.donorsSnapshot),e(j,{donorsCorrect:!0})}})})})]},j)})})]})})})]})}const jp=7,Xy=[1,3,3],$y=1500,Yy=()=>{var t;return typeof window<"u"&&((t=window.matchMedia)==null?void 0:t.call(window,"(prefers-reduced-motion: reduce)").matches)};function qy({target:t}){const[e,n]=Q.useState("0"),[i,r]=Q.useState(null);Q.useEffect(()=>{if(!(i!==null||e===t)){if(Yy()){n(t);return}r(String((Number(e)+1)%10))}},[e,i,t]);const s=()=>{n(i),r(null)};return y.jsxs("span",{className:"flap",children:[y.jsx("span",{className:"flap-half flap-top",children:y.jsx("span",{children:i??e})}),y.jsx("span",{className:"flap-half flap-bot",children:y.jsx("span",{children:e})}),i!==null&&y.jsxs(y.Fragment,{children:[y.jsx("span",{className:"flap-leaf flap-top flap-fall",children:y.jsx("span",{children:e})}),y.jsx("span",{className:"flap-leaf flap-bot flap-land",onAnimationEnd:s,children:y.jsx("span",{children:i})})]})]})}function Ky(t){const e=new Date(`${t}T00:00:00Z`);return Number.isNaN(e.getTime())?null:e.toLocaleDateString("en-GB",{month:"long",year:"numeric",timeZone:"UTC"})}function Zy({refreshKey:t}){const[e,n]=Q.useState(null);if(Q.useEffect(()=>{let l=!0;const c=setTimeout(()=>St.stats().then(d=>l&&n(d)).catch(()=>{}),t?$y:0);return()=>{l=!1,clearTimeout(c)}},[t]),!e||typeof e.structures_built!="number")return null;const i=Math.max(0,Math.floor(e.structures_built)),r=String(i).padStart(jp,"0").slice(-jp).split(""),s=e.since?Ky(e.since):null,o=s?`structures built since ${s}`:"structures built";let a=0;return y.jsxs("div",{className:"flip-counter",children:[y.jsx("span",{className:"sr-only",children:`${i.toLocaleString("en-GB")} ${o}`}),y.jsx("span",{className:"flip-board","aria-hidden":"true",children:Xy.map((l,c)=>y.jsx("span",{className:"flip-group",children:r.slice(a,a+=l).map((d,h)=>y.jsx(qy,{target:d},h))},c))}),y.jsx("span",{"aria-hidden":"true",children:o})]})}function gl(){return typeof window<"u"&&window.matchMedia("(prefers-reduced-motion: reduce)").matches}const Bi=8,Jy=120,Qy=.25;function Qc(t,e,n,i){const r=Math.max(0,Math.min(i.right,innerWidth)-Math.max(i.left,0)),s=Math.max(0,Math.min(i.bottom,innerHeight)-Math.max(i.top,0));if(!r||!s)return 0;const o=Math.max(0,Math.min(n.right,i.right)-Math.max(n.left,i.left)),a=Math.max(0,Math.min(t+e,i.bottom)-Math.max(t,i.top));return o*a/(r*s)}const Mo=t=>!!document.querySelector(`[data-tour="${t}"]`),eu=t=>!!t&&(!t.target||Mo(t.target));function eS({open:t,steps:e,actions:n,onClose:i}){const[r,s]=Q.useState(0),[o,a]=Q.useState(null),[l,c]=Q.useState(null),d=Q.useRef(null),[h,f]=Q.useState(null),p=(A,P)=>{let E=P+A;for(;E>=0&&E<e.length&&!eu(e[E]);)E+=A;return E};function g(){i==null||i()}function x(){const A=p(1,r);A>=e.length?g():s(A)}function m(){const A=p(-1,r);A>=0&&s(A)}Q.useEffect(()=>{if(!t)return;let A=0;for(;A<e.length&&!eu(e[A]);)A+=1;s(A<e.length?A:0)},[t,e]);const u=e[r],_=p(1,r)>=e.length;Q.useEffect(()=>{if(!t||!u||(u.action&&(n!=null&&n[u.action])&&n[u.action](),!u.waitFor&&!u.waitGone))return;const A=()=>{(u.waitFor?Mo(u.waitFor):!Mo(u.waitGone))&&(clearInterval(P),x())},P=setInterval(A,300);return A(),()=>clearInterval(P)},[t,u]),Q.useLayoutEffect(()=>{if(!t||!u)return;const A=()=>{const E=u.target?document.querySelector(`[data-tour="${u.target}"]`):null,S=E?E.getBoundingClientRect():null;if(a(S?{top:S.top,left:S.left,width:S.width,height:S.height}:null),!Mo("complex-table")){const D=document.querySelector('[data-tour="input-card"]'),X=D?D.getBoundingClientRect().bottom:window.innerHeight*.3;c(Math.max(80,Math.min(X+16,window.innerHeight-220)))}},P=u.target?document.querySelector(`[data-tour="${u.target}"]`):null;return P&&P.scrollIntoView({block:"center",behavior:gl()?"auto":"smooth"}),A(),window.addEventListener("resize",A),window.addEventListener("scroll",A,!0),()=>{window.removeEventListener("resize",A),window.removeEventListener("scroll",A,!0)}},[t,u]),Q.useEffect(()=>{if(!t)return;const A=P=>{P.key==="Escape"?g():(P.key==="Enter"||P.key==="ArrowRight")&&!(u!=null&&u.waitFor)&&!(u!=null&&u.waitGone)?x():P.key==="ArrowLeft"&&m()};return window.addEventListener("keydown",A),()=>window.removeEventListener("keydown",A)});const v=t&&Mo("complex-table");if(Q.useLayoutEffect(()=>{const A=d.current;let P=null;if(t&&A&&o){const E=A.offsetHeight,S=innerHeight,D=12,X=A.getBoundingClientRect(),H={top:o.top-Bi,bottom:o.top+o.height+Bi,left:o.left-Bi,right:o.left+o.width+Bi},U=J=>Math.max(8,Math.min(S-E-8,J)),Y=v?S-28-E:l??S*.34,V=H.bottom-H.top<Jy?0:Qy;Qc(Y,E,X,H)>V&&(P=[H.bottom+D,H.top-D-E,8,S-E-8].map(U).reduce((N,j)=>Qc(j,E,X,H)<Qc(N,E,X,H)?j:N),P=Math.round(P))}P!==h&&f(P)}),!t||!u)return null;const M=e.filter(eu),R=M.indexOf(u)+1,C=!!u.interactive;return y.jsxs("div",{className:"tour-root",role:"dialog","aria-modal":"true","aria-label":"Guided tour",children:[y.jsx("div",{className:"tour-blocker"+(o?"":" dim")+(C?" pass":"")}),o&&y.jsx("div",{className:"tour-highlight",style:{top:o.top-Bi,left:o.left-Bi,width:o.width+Bi*2,height:o.height+Bi*2}}),y.jsxs("div",{ref:d,className:"tour-tooltip "+(v?"docked":"free"),style:h!=null?{top:h,bottom:"auto"}:v?void 0:{top:l??"34%"},children:[y.jsxs("div",{className:"tour-count mono",children:[R," / ",M.length]}),y.jsx("h3",{className:"tour-title",children:u.title}),y.jsx("p",{className:"tour-body",children:u.body}),y.jsxs("div",{className:"tour-nav",children:[y.jsx("button",{className:"ghost",onClick:g,children:"Skip"}),y.jsxs("div",{className:"tour-nav-right",children:[R>1&&y.jsx("button",{className:"ghost",onClick:m,children:"Back"}),u.waitFor||u.waitGone?y.jsxs("span",{className:"tour-wait",children:[y.jsx("span",{className:"tour-wait-dot"}),u.waitLabel||"Your turn"]}):y.jsx("button",{className:"primary",onClick:x,children:_?"Done":"Next"})]})]})]})]})}const tS={flask:y.jsxs(y.Fragment,{children:[y.jsx("path",{d:"M10 2v7.527a2 2 0 0 1-.211.896L4.72 20.55a1 1 0 0 0 .9 1.45h12.76a1 1 0 0 0 .9-1.45l-5.069-10.127A2 2 0 0 1 14 9.527V2"}),y.jsx("path",{d:"M8.5 2h7"}),y.jsx("path",{d:"M7 16h10"})]}),timer:y.jsxs(y.Fragment,{children:[y.jsx("line",{x1:"10",x2:"14",y1:"2",y2:"2"}),y.jsx("line",{x1:"12",x2:"15",y1:"14",y2:"11"}),y.jsx("circle",{cx:"12",cy:"14",r:"8"})]})};function tu({name:t,size:e=15,className:n="ui-icon"}){return y.jsx("svg",{className:n,width:e,height:e,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor",strokeWidth:"2",strokeLinecap:"round",strokeLinejoin:"round","aria-hidden":"true",focusable:"false",children:tS[t]})}/**
 * @license
 * Copyright 2010-2024 Three.js Authors
 * SPDX-License-Identifier: MIT
 */const yf="171",Ds={ROTATE:0,DOLLY:1,PAN:2},Ts={ROTATE:0,PAN:1,DOLLY_PAN:2,DOLLY_ROTATE:3},nS=0,Wp=1,iS=2,Ev=1,rS=2,Si=3,hr=0,gn=1,wi=2,lr=0,Is=1,Xp=2,$p=3,Yp=4,sS=5,br=100,oS=101,aS=102,lS=103,cS=104,uS=200,dS=201,hS=202,fS=203,Od=204,Fd=205,pS=206,mS=207,gS=208,_S=209,vS=210,xS=211,yS=212,SS=213,MS=214,kd=0,Bd=1,zd=2,js=3,Hd=4,Vd=5,Gd=6,jd=7,wv=0,ES=1,wS=2,cr=0,TS=1,AS=2,CS=3,bS=4,RS=5,PS=6,LS=7,Tv=300,Ws=301,Xs=302,Wd=303,Xd=304,yc=306,$d=1e3,Dr=1001,Yd=1002,ni=1003,NS=1004,La=1005,li=1006,nu=1007,Ir=1008,Ui=1009,Av=1010,Cv=1011,ea=1012,Sf=1013,Vr=1014,Ci=1015,oa=1016,Mf=1017,Ef=1018,$s=1020,bv=35902,Rv=1021,Pv=1022,Qn=1023,Lv=1024,Nv=1025,Us=1026,Ys=1027,Dv=1028,wf=1029,Iv=1030,Tf=1031,Af=1033,_l=33776,vl=33777,xl=33778,yl=33779,qd=35840,Kd=35841,Zd=35842,Jd=35843,Qd=36196,eh=37492,th=37496,nh=37808,ih=37809,rh=37810,sh=37811,oh=37812,ah=37813,lh=37814,ch=37815,uh=37816,dh=37817,hh=37818,fh=37819,ph=37820,mh=37821,Sl=36492,gh=36494,_h=36495,Uv=36283,vh=36284,xh=36285,yh=36286,DS=3200,IS=3201,Ov=0,US=1,Zi="",In="srgb",qs="srgb-linear",Kl="linear",ft="srgb",Zr=7680,qp=519,OS=512,FS=513,kS=514,Fv=515,BS=516,zS=517,HS=518,VS=519,Kp=35044,Zp="300 es",bi=2e3,Zl=2001;class $r{addEventListener(e,n){this._listeners===void 0&&(this._listeners={});const i=this._listeners;i[e]===void 0&&(i[e]=[]),i[e].indexOf(n)===-1&&i[e].push(n)}hasEventListener(e,n){if(this._listeners===void 0)return!1;const i=this._listeners;return i[e]!==void 0&&i[e].indexOf(n)!==-1}removeEventListener(e,n){if(this._listeners===void 0)return;const r=this._listeners[e];if(r!==void 0){const s=r.indexOf(n);s!==-1&&r.splice(s,1)}}dispatchEvent(e){if(this._listeners===void 0)return;const i=this._listeners[e.type];if(i!==void 0){e.target=this;const r=i.slice(0);for(let s=0,o=r.length;s<o;s++)r[s].call(this,e);e.target=null}}}const Zt=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"],Ml=Math.PI/180,Sh=180/Math.PI;function aa(){const t=Math.random()*4294967295|0,e=Math.random()*4294967295|0,n=Math.random()*4294967295|0,i=Math.random()*4294967295|0;return(Zt[t&255]+Zt[t>>8&255]+Zt[t>>16&255]+Zt[t>>24&255]+"-"+Zt[e&255]+Zt[e>>8&255]+"-"+Zt[e>>16&15|64]+Zt[e>>24&255]+"-"+Zt[n&63|128]+Zt[n>>8&255]+"-"+Zt[n>>16&255]+Zt[n>>24&255]+Zt[i&255]+Zt[i>>8&255]+Zt[i>>16&255]+Zt[i>>24&255]).toLowerCase()}function et(t,e,n){return Math.max(e,Math.min(n,t))}function GS(t,e){return(t%e+e)%e}function iu(t,e,n){return(1-n)*t+n*e}function ho(t,e){switch(e.constructor){case Float32Array:return t;case Uint32Array:return t/4294967295;case Uint16Array:return t/65535;case Uint8Array:return t/255;case Int32Array:return Math.max(t/2147483647,-1);case Int16Array:return Math.max(t/32767,-1);case Int8Array:return Math.max(t/127,-1);default:throw new Error("Invalid component type.")}}function cn(t,e){switch(e.constructor){case Float32Array:return t;case Uint32Array:return Math.round(t*4294967295);case Uint16Array:return Math.round(t*65535);case Uint8Array:return Math.round(t*255);case Int32Array:return Math.round(t*2147483647);case Int16Array:return Math.round(t*32767);case Int8Array:return Math.round(t*127);default:throw new Error("Invalid component type.")}}const jS={DEG2RAD:Ml};class Fe{constructor(e=0,n=0){Fe.prototype.isVector2=!0,this.x=e,this.y=n}get width(){return this.x}set width(e){this.x=e}get height(){return this.y}set height(e){this.y=e}set(e,n){return this.x=e,this.y=n,this}setScalar(e){return this.x=e,this.y=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setComponent(e,n){switch(e){case 0:this.x=n;break;case 1:this.y=n;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y)}copy(e){return this.x=e.x,this.y=e.y,this}add(e){return this.x+=e.x,this.y+=e.y,this}addScalar(e){return this.x+=e,this.y+=e,this}addVectors(e,n){return this.x=e.x+n.x,this.y=e.y+n.y,this}addScaledVector(e,n){return this.x+=e.x*n,this.y+=e.y*n,this}sub(e){return this.x-=e.x,this.y-=e.y,this}subScalar(e){return this.x-=e,this.y-=e,this}subVectors(e,n){return this.x=e.x-n.x,this.y=e.y-n.y,this}multiply(e){return this.x*=e.x,this.y*=e.y,this}multiplyScalar(e){return this.x*=e,this.y*=e,this}divide(e){return this.x/=e.x,this.y/=e.y,this}divideScalar(e){return this.multiplyScalar(1/e)}applyMatrix3(e){const n=this.x,i=this.y,r=e.elements;return this.x=r[0]*n+r[3]*i+r[6],this.y=r[1]*n+r[4]*i+r[7],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this}clamp(e,n){return this.x=et(this.x,e.x,n.x),this.y=et(this.y,e.y,n.y),this}clampScalar(e,n){return this.x=et(this.x,e,n),this.y=et(this.y,e,n),this}clampLength(e,n){const i=this.length();return this.divideScalar(i||1).multiplyScalar(et(i,e,n))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(e){return this.x*e.x+this.y*e.y}cross(e){return this.x*e.y-this.y*e.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(e){const n=Math.sqrt(this.lengthSq()*e.lengthSq());if(n===0)return Math.PI/2;const i=this.dot(e)/n;return Math.acos(et(i,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){const n=this.x-e.x,i=this.y-e.y;return n*n+i*i}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,n){return this.x+=(e.x-this.x)*n,this.y+=(e.y-this.y)*n,this}lerpVectors(e,n,i){return this.x=e.x+(n.x-e.x)*i,this.y=e.y+(n.y-e.y)*i,this}equals(e){return e.x===this.x&&e.y===this.y}fromArray(e,n=0){return this.x=e[n],this.y=e[n+1],this}toArray(e=[],n=0){return e[n]=this.x,e[n+1]=this.y,e}fromBufferAttribute(e,n){return this.x=e.getX(n),this.y=e.getY(n),this}rotateAround(e,n){const i=Math.cos(n),r=Math.sin(n),s=this.x-e.x,o=this.y-e.y;return this.x=s*i-o*r+e.x,this.y=s*r+o*i+e.y,this}random(){return this.x=Math.random(),this.y=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y}}class Ze{constructor(e,n,i,r,s,o,a,l,c){Ze.prototype.isMatrix3=!0,this.elements=[1,0,0,0,1,0,0,0,1],e!==void 0&&this.set(e,n,i,r,s,o,a,l,c)}set(e,n,i,r,s,o,a,l,c){const d=this.elements;return d[0]=e,d[1]=r,d[2]=a,d[3]=n,d[4]=s,d[5]=l,d[6]=i,d[7]=o,d[8]=c,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(e){const n=this.elements,i=e.elements;return n[0]=i[0],n[1]=i[1],n[2]=i[2],n[3]=i[3],n[4]=i[4],n[5]=i[5],n[6]=i[6],n[7]=i[7],n[8]=i[8],this}extractBasis(e,n,i){return e.setFromMatrix3Column(this,0),n.setFromMatrix3Column(this,1),i.setFromMatrix3Column(this,2),this}setFromMatrix4(e){const n=e.elements;return this.set(n[0],n[4],n[8],n[1],n[5],n[9],n[2],n[6],n[10]),this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,n){const i=e.elements,r=n.elements,s=this.elements,o=i[0],a=i[3],l=i[6],c=i[1],d=i[4],h=i[7],f=i[2],p=i[5],g=i[8],x=r[0],m=r[3],u=r[6],_=r[1],v=r[4],M=r[7],R=r[2],C=r[5],A=r[8];return s[0]=o*x+a*_+l*R,s[3]=o*m+a*v+l*C,s[6]=o*u+a*M+l*A,s[1]=c*x+d*_+h*R,s[4]=c*m+d*v+h*C,s[7]=c*u+d*M+h*A,s[2]=f*x+p*_+g*R,s[5]=f*m+p*v+g*C,s[8]=f*u+p*M+g*A,this}multiplyScalar(e){const n=this.elements;return n[0]*=e,n[3]*=e,n[6]*=e,n[1]*=e,n[4]*=e,n[7]*=e,n[2]*=e,n[5]*=e,n[8]*=e,this}determinant(){const e=this.elements,n=e[0],i=e[1],r=e[2],s=e[3],o=e[4],a=e[5],l=e[6],c=e[7],d=e[8];return n*o*d-n*a*c-i*s*d+i*a*l+r*s*c-r*o*l}invert(){const e=this.elements,n=e[0],i=e[1],r=e[2],s=e[3],o=e[4],a=e[5],l=e[6],c=e[7],d=e[8],h=d*o-a*c,f=a*l-d*s,p=c*s-o*l,g=n*h+i*f+r*p;if(g===0)return this.set(0,0,0,0,0,0,0,0,0);const x=1/g;return e[0]=h*x,e[1]=(r*c-d*i)*x,e[2]=(a*i-r*o)*x,e[3]=f*x,e[4]=(d*n-r*l)*x,e[5]=(r*s-a*n)*x,e[6]=p*x,e[7]=(i*l-c*n)*x,e[8]=(o*n-i*s)*x,this}transpose(){let e;const n=this.elements;return e=n[1],n[1]=n[3],n[3]=e,e=n[2],n[2]=n[6],n[6]=e,e=n[5],n[5]=n[7],n[7]=e,this}getNormalMatrix(e){return this.setFromMatrix4(e).invert().transpose()}transposeIntoArray(e){const n=this.elements;return e[0]=n[0],e[1]=n[3],e[2]=n[6],e[3]=n[1],e[4]=n[4],e[5]=n[7],e[6]=n[2],e[7]=n[5],e[8]=n[8],this}setUvTransform(e,n,i,r,s,o,a){const l=Math.cos(s),c=Math.sin(s);return this.set(i*l,i*c,-i*(l*o+c*a)+o+e,-r*c,r*l,-r*(-c*o+l*a)+a+n,0,0,1),this}scale(e,n){return this.premultiply(ru.makeScale(e,n)),this}rotate(e){return this.premultiply(ru.makeRotation(-e)),this}translate(e,n){return this.premultiply(ru.makeTranslation(e,n)),this}makeTranslation(e,n){return e.isVector2?this.set(1,0,e.x,0,1,e.y,0,0,1):this.set(1,0,e,0,1,n,0,0,1),this}makeRotation(e){const n=Math.cos(e),i=Math.sin(e);return this.set(n,-i,0,i,n,0,0,0,1),this}makeScale(e,n){return this.set(e,0,0,0,n,0,0,0,1),this}equals(e){const n=this.elements,i=e.elements;for(let r=0;r<9;r++)if(n[r]!==i[r])return!1;return!0}fromArray(e,n=0){for(let i=0;i<9;i++)this.elements[i]=e[i+n];return this}toArray(e=[],n=0){const i=this.elements;return e[n]=i[0],e[n+1]=i[1],e[n+2]=i[2],e[n+3]=i[3],e[n+4]=i[4],e[n+5]=i[5],e[n+6]=i[6],e[n+7]=i[7],e[n+8]=i[8],e}clone(){return new this.constructor().fromArray(this.elements)}}const ru=new Ze;function kv(t){for(let e=t.length-1;e>=0;--e)if(t[e]>=65535)return!0;return!1}function Jl(t){return document.createElementNS("http://www.w3.org/1999/xhtml",t)}function WS(){const t=Jl("canvas");return t.style.display="block",t}const Jp={};function hs(t){t in Jp||(Jp[t]=!0,console.warn(t))}function XS(t,e,n){return new Promise(function(i,r){function s(){switch(t.clientWaitSync(e,t.SYNC_FLUSH_COMMANDS_BIT,0)){case t.WAIT_FAILED:r();break;case t.TIMEOUT_EXPIRED:setTimeout(s,n);break;default:i()}}setTimeout(s,n)})}function $S(t){const e=t.elements;e[2]=.5*e[2]+.5*e[3],e[6]=.5*e[6]+.5*e[7],e[10]=.5*e[10]+.5*e[11],e[14]=.5*e[14]+.5*e[15]}function YS(t){const e=t.elements;e[11]===-1?(e[10]=-e[10]-1,e[14]=-e[14]):(e[10]=-e[10],e[14]=-e[14]+1)}const Qp=new Ze().set(.4123908,.3575843,.1804808,.212639,.7151687,.0721923,.0193308,.1191948,.9505322),em=new Ze().set(3.2409699,-1.5373832,-.4986108,-.9692436,1.8759675,.0415551,.0556301,-.203977,1.0569715);function qS(){const t={enabled:!0,workingColorSpace:qs,spaces:{},convert:function(r,s,o){return this.enabled===!1||s===o||!s||!o||(this.spaces[s].transfer===ft&&(r.r=Pi(r.r),r.g=Pi(r.g),r.b=Pi(r.b)),this.spaces[s].primaries!==this.spaces[o].primaries&&(r.applyMatrix3(this.spaces[s].toXYZ),r.applyMatrix3(this.spaces[o].fromXYZ)),this.spaces[o].transfer===ft&&(r.r=Os(r.r),r.g=Os(r.g),r.b=Os(r.b))),r},fromWorkingColorSpace:function(r,s){return this.convert(r,this.workingColorSpace,s)},toWorkingColorSpace:function(r,s){return this.convert(r,s,this.workingColorSpace)},getPrimaries:function(r){return this.spaces[r].primaries},getTransfer:function(r){return r===Zi?Kl:this.spaces[r].transfer},getLuminanceCoefficients:function(r,s=this.workingColorSpace){return r.fromArray(this.spaces[s].luminanceCoefficients)},define:function(r){Object.assign(this.spaces,r)},_getMatrix:function(r,s,o){return r.copy(this.spaces[s].toXYZ).multiply(this.spaces[o].fromXYZ)},_getDrawingBufferColorSpace:function(r){return this.spaces[r].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(r=this.workingColorSpace){return this.spaces[r].workingColorSpaceConfig.unpackColorSpace}},e=[.64,.33,.3,.6,.15,.06],n=[.2126,.7152,.0722],i=[.3127,.329];return t.define({[qs]:{primaries:e,whitePoint:i,transfer:Kl,toXYZ:Qp,fromXYZ:em,luminanceCoefficients:n,workingColorSpaceConfig:{unpackColorSpace:In},outputColorSpaceConfig:{drawingBufferColorSpace:In}},[In]:{primaries:e,whitePoint:i,transfer:ft,toXYZ:Qp,fromXYZ:em,luminanceCoefficients:n,outputColorSpaceConfig:{drawingBufferColorSpace:In}}}),t}const lt=qS();function Pi(t){return t<.04045?t*.0773993808:Math.pow(t*.9478672986+.0521327014,2.4)}function Os(t){return t<.0031308?t*12.92:1.055*Math.pow(t,.41666)-.055}let Jr;class KS{static getDataURL(e){if(/^data:/i.test(e.src)||typeof HTMLCanvasElement>"u")return e.src;let n;if(e instanceof HTMLCanvasElement)n=e;else{Jr===void 0&&(Jr=Jl("canvas")),Jr.width=e.width,Jr.height=e.height;const i=Jr.getContext("2d");e instanceof ImageData?i.putImageData(e,0,0):i.drawImage(e,0,0,e.width,e.height),n=Jr}return n.width>2048||n.height>2048?(console.warn("THREE.ImageUtils.getDataURL: Image converted to jpg for performance reasons",e),n.toDataURL("image/jpeg",.6)):n.toDataURL("image/png")}static sRGBToLinear(e){if(typeof HTMLImageElement<"u"&&e instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&e instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&e instanceof ImageBitmap){const n=Jl("canvas");n.width=e.width,n.height=e.height;const i=n.getContext("2d");i.drawImage(e,0,0,e.width,e.height);const r=i.getImageData(0,0,e.width,e.height),s=r.data;for(let o=0;o<s.length;o++)s[o]=Pi(s[o]/255)*255;return i.putImageData(r,0,0),n}else if(e.data){const n=e.data.slice(0);for(let i=0;i<n.length;i++)n instanceof Uint8Array||n instanceof Uint8ClampedArray?n[i]=Math.floor(Pi(n[i]/255)*255):n[i]=Pi(n[i]);return{data:n,width:e.width,height:e.height}}else return console.warn("THREE.ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),e}}let ZS=0;class Bv{constructor(e=null){this.isSource=!0,Object.defineProperty(this,"id",{value:ZS++}),this.uuid=aa(),this.data=e,this.dataReady=!0,this.version=0}set needsUpdate(e){e===!0&&this.version++}toJSON(e){const n=e===void 0||typeof e=="string";if(!n&&e.images[this.uuid]!==void 0)return e.images[this.uuid];const i={uuid:this.uuid,url:""},r=this.data;if(r!==null){let s;if(Array.isArray(r)){s=[];for(let o=0,a=r.length;o<a;o++)r[o].isDataTexture?s.push(su(r[o].image)):s.push(su(r[o]))}else s=su(r);i.url=s}return n||(e.images[this.uuid]=i),i}}function su(t){return typeof HTMLImageElement<"u"&&t instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&t instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&t instanceof ImageBitmap?KS.getDataURL(t):t.data?{data:Array.from(t.data),width:t.width,height:t.height,type:t.data.constructor.name}:(console.warn("THREE.Texture: Unable to serialize Texture."),{})}let JS=0;class _n extends $r{constructor(e=_n.DEFAULT_IMAGE,n=_n.DEFAULT_MAPPING,i=Dr,r=Dr,s=li,o=Ir,a=Qn,l=Ui,c=_n.DEFAULT_ANISOTROPY,d=Zi){super(),this.isTexture=!0,Object.defineProperty(this,"id",{value:JS++}),this.uuid=aa(),this.name="",this.source=new Bv(e),this.mipmaps=[],this.mapping=n,this.channel=0,this.wrapS=i,this.wrapT=r,this.magFilter=s,this.minFilter=o,this.anisotropy=c,this.format=a,this.internalFormat=null,this.type=l,this.offset=new Fe(0,0),this.repeat=new Fe(1,1),this.center=new Fe(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new Ze,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=d,this.userData={},this.version=0,this.onUpdate=null,this.isRenderTargetTexture=!1,this.pmremVersion=0}get image(){return this.source.data}set image(e=null){this.source.data=e}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}clone(){return new this.constructor().copy(this)}copy(e){return this.name=e.name,this.source=e.source,this.mipmaps=e.mipmaps.slice(0),this.mapping=e.mapping,this.channel=e.channel,this.wrapS=e.wrapS,this.wrapT=e.wrapT,this.magFilter=e.magFilter,this.minFilter=e.minFilter,this.anisotropy=e.anisotropy,this.format=e.format,this.internalFormat=e.internalFormat,this.type=e.type,this.offset.copy(e.offset),this.repeat.copy(e.repeat),this.center.copy(e.center),this.rotation=e.rotation,this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrix.copy(e.matrix),this.generateMipmaps=e.generateMipmaps,this.premultiplyAlpha=e.premultiplyAlpha,this.flipY=e.flipY,this.unpackAlignment=e.unpackAlignment,this.colorSpace=e.colorSpace,this.userData=JSON.parse(JSON.stringify(e.userData)),this.needsUpdate=!0,this}toJSON(e){const n=e===void 0||typeof e=="string";if(!n&&e.textures[this.uuid]!==void 0)return e.textures[this.uuid];const i={metadata:{version:4.6,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(e).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};return Object.keys(this.userData).length>0&&(i.userData=this.userData),n||(e.textures[this.uuid]=i),i}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(e){if(this.mapping!==Tv)return e;if(e.applyMatrix3(this.matrix),e.x<0||e.x>1)switch(this.wrapS){case $d:e.x=e.x-Math.floor(e.x);break;case Dr:e.x=e.x<0?0:1;break;case Yd:Math.abs(Math.floor(e.x)%2)===1?e.x=Math.ceil(e.x)-e.x:e.x=e.x-Math.floor(e.x);break}if(e.y<0||e.y>1)switch(this.wrapT){case $d:e.y=e.y-Math.floor(e.y);break;case Dr:e.y=e.y<0?0:1;break;case Yd:Math.abs(Math.floor(e.y)%2)===1?e.y=Math.ceil(e.y)-e.y:e.y=e.y-Math.floor(e.y);break}return this.flipY&&(e.y=1-e.y),e}set needsUpdate(e){e===!0&&(this.version++,this.source.needsUpdate=!0)}set needsPMREMUpdate(e){e===!0&&this.pmremVersion++}}_n.DEFAULT_IMAGE=null;_n.DEFAULT_MAPPING=Tv;_n.DEFAULT_ANISOTROPY=1;class Rt{constructor(e=0,n=0,i=0,r=1){Rt.prototype.isVector4=!0,this.x=e,this.y=n,this.z=i,this.w=r}get width(){return this.z}set width(e){this.z=e}get height(){return this.w}set height(e){this.w=e}set(e,n,i,r){return this.x=e,this.y=n,this.z=i,this.w=r,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this.w=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setW(e){return this.w=e,this}setComponent(e,n){switch(e){case 0:this.x=n;break;case 1:this.y=n;break;case 2:this.z=n;break;case 3:this.w=n;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this.w=e.w!==void 0?e.w:1,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this.w+=e.w,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this.w+=e,this}addVectors(e,n){return this.x=e.x+n.x,this.y=e.y+n.y,this.z=e.z+n.z,this.w=e.w+n.w,this}addScaledVector(e,n){return this.x+=e.x*n,this.y+=e.y*n,this.z+=e.z*n,this.w+=e.w*n,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this.w-=e.w,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this.w-=e,this}subVectors(e,n){return this.x=e.x-n.x,this.y=e.y-n.y,this.z=e.z-n.z,this.w=e.w-n.w,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this.w*=e.w,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this.w*=e,this}applyMatrix4(e){const n=this.x,i=this.y,r=this.z,s=this.w,o=e.elements;return this.x=o[0]*n+o[4]*i+o[8]*r+o[12]*s,this.y=o[1]*n+o[5]*i+o[9]*r+o[13]*s,this.z=o[2]*n+o[6]*i+o[10]*r+o[14]*s,this.w=o[3]*n+o[7]*i+o[11]*r+o[15]*s,this}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this.w/=e.w,this}divideScalar(e){return this.multiplyScalar(1/e)}setAxisAngleFromQuaternion(e){this.w=2*Math.acos(e.w);const n=Math.sqrt(1-e.w*e.w);return n<1e-4?(this.x=1,this.y=0,this.z=0):(this.x=e.x/n,this.y=e.y/n,this.z=e.z/n),this}setAxisAngleFromRotationMatrix(e){let n,i,r,s;const l=e.elements,c=l[0],d=l[4],h=l[8],f=l[1],p=l[5],g=l[9],x=l[2],m=l[6],u=l[10];if(Math.abs(d-f)<.01&&Math.abs(h-x)<.01&&Math.abs(g-m)<.01){if(Math.abs(d+f)<.1&&Math.abs(h+x)<.1&&Math.abs(g+m)<.1&&Math.abs(c+p+u-3)<.1)return this.set(1,0,0,0),this;n=Math.PI;const v=(c+1)/2,M=(p+1)/2,R=(u+1)/2,C=(d+f)/4,A=(h+x)/4,P=(g+m)/4;return v>M&&v>R?v<.01?(i=0,r=.707106781,s=.707106781):(i=Math.sqrt(v),r=C/i,s=A/i):M>R?M<.01?(i=.707106781,r=0,s=.707106781):(r=Math.sqrt(M),i=C/r,s=P/r):R<.01?(i=.707106781,r=.707106781,s=0):(s=Math.sqrt(R),i=A/s,r=P/s),this.set(i,r,s,n),this}let _=Math.sqrt((m-g)*(m-g)+(h-x)*(h-x)+(f-d)*(f-d));return Math.abs(_)<.001&&(_=1),this.x=(m-g)/_,this.y=(h-x)/_,this.z=(f-d)/_,this.w=Math.acos((c+p+u-1)/2),this}setFromMatrixPosition(e){const n=e.elements;return this.x=n[12],this.y=n[13],this.z=n[14],this.w=n[15],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this.w=Math.min(this.w,e.w),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this.w=Math.max(this.w,e.w),this}clamp(e,n){return this.x=et(this.x,e.x,n.x),this.y=et(this.y,e.y,n.y),this.z=et(this.z,e.z,n.z),this.w=et(this.w,e.w,n.w),this}clampScalar(e,n){return this.x=et(this.x,e,n),this.y=et(this.y,e,n),this.z=et(this.z,e,n),this.w=et(this.w,e,n),this}clampLength(e,n){const i=this.length();return this.divideScalar(i||1).multiplyScalar(et(i,e,n))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z+this.w*e.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,n){return this.x+=(e.x-this.x)*n,this.y+=(e.y-this.y)*n,this.z+=(e.z-this.z)*n,this.w+=(e.w-this.w)*n,this}lerpVectors(e,n,i){return this.x=e.x+(n.x-e.x)*i,this.y=e.y+(n.y-e.y)*i,this.z=e.z+(n.z-e.z)*i,this.w=e.w+(n.w-e.w)*i,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z&&e.w===this.w}fromArray(e,n=0){return this.x=e[n],this.y=e[n+1],this.z=e[n+2],this.w=e[n+3],this}toArray(e=[],n=0){return e[n]=this.x,e[n+1]=this.y,e[n+2]=this.z,e[n+3]=this.w,e}fromBufferAttribute(e,n){return this.x=e.getX(n),this.y=e.getY(n),this.z=e.getZ(n),this.w=e.getW(n),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this.w=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}}class QS extends $r{constructor(e=1,n=1,i={}){super(),this.isRenderTarget=!0,this.width=e,this.height=n,this.depth=1,this.scissor=new Rt(0,0,e,n),this.scissorTest=!1,this.viewport=new Rt(0,0,e,n);const r={width:e,height:n,depth:1};i=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:li,depthBuffer:!0,stencilBuffer:!1,resolveDepthBuffer:!0,resolveStencilBuffer:!0,depthTexture:null,samples:0,count:1},i);const s=new _n(r,i.mapping,i.wrapS,i.wrapT,i.magFilter,i.minFilter,i.format,i.type,i.anisotropy,i.colorSpace);s.flipY=!1,s.generateMipmaps=i.generateMipmaps,s.internalFormat=i.internalFormat,this.textures=[];const o=i.count;for(let a=0;a<o;a++)this.textures[a]=s.clone(),this.textures[a].isRenderTargetTexture=!0;this.depthBuffer=i.depthBuffer,this.stencilBuffer=i.stencilBuffer,this.resolveDepthBuffer=i.resolveDepthBuffer,this.resolveStencilBuffer=i.resolveStencilBuffer,this.depthTexture=i.depthTexture,this.samples=i.samples}get texture(){return this.textures[0]}set texture(e){this.textures[0]=e}setSize(e,n,i=1){if(this.width!==e||this.height!==n||this.depth!==i){this.width=e,this.height=n,this.depth=i;for(let r=0,s=this.textures.length;r<s;r++)this.textures[r].image.width=e,this.textures[r].image.height=n,this.textures[r].image.depth=i;this.dispose()}this.viewport.set(0,0,e,n),this.scissor.set(0,0,e,n)}clone(){return new this.constructor().copy(this)}copy(e){this.width=e.width,this.height=e.height,this.depth=e.depth,this.scissor.copy(e.scissor),this.scissorTest=e.scissorTest,this.viewport.copy(e.viewport),this.textures.length=0;for(let i=0,r=e.textures.length;i<r;i++)this.textures[i]=e.textures[i].clone(),this.textures[i].isRenderTargetTexture=!0;const n=Object.assign({},e.texture.image);return this.texture.source=new Bv(n),this.depthBuffer=e.depthBuffer,this.stencilBuffer=e.stencilBuffer,this.resolveDepthBuffer=e.resolveDepthBuffer,this.resolveStencilBuffer=e.resolveStencilBuffer,e.depthTexture!==null&&(this.depthTexture=e.depthTexture.clone()),this.samples=e.samples,this}dispose(){this.dispatchEvent({type:"dispose"})}}class Gr extends QS{constructor(e=1,n=1,i={}){super(e,n,i),this.isWebGLRenderTarget=!0}}class zv extends _n{constructor(e=null,n=1,i=1,r=1){super(null),this.isDataArrayTexture=!0,this.image={data:e,width:n,height:i,depth:r},this.magFilter=ni,this.minFilter=ni,this.wrapR=Dr,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}addLayerUpdate(e){this.layerUpdates.add(e)}clearLayerUpdates(){this.layerUpdates.clear()}}class eM extends _n{constructor(e=null,n=1,i=1,r=1){super(null),this.isData3DTexture=!0,this.image={data:e,width:n,height:i,depth:r},this.magFilter=ni,this.minFilter=ni,this.wrapR=Dr,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}}class jr{constructor(e=0,n=0,i=0,r=1){this.isQuaternion=!0,this._x=e,this._y=n,this._z=i,this._w=r}static slerpFlat(e,n,i,r,s,o,a){let l=i[r+0],c=i[r+1],d=i[r+2],h=i[r+3];const f=s[o+0],p=s[o+1],g=s[o+2],x=s[o+3];if(a===0){e[n+0]=l,e[n+1]=c,e[n+2]=d,e[n+3]=h;return}if(a===1){e[n+0]=f,e[n+1]=p,e[n+2]=g,e[n+3]=x;return}if(h!==x||l!==f||c!==p||d!==g){let m=1-a;const u=l*f+c*p+d*g+h*x,_=u>=0?1:-1,v=1-u*u;if(v>Number.EPSILON){const R=Math.sqrt(v),C=Math.atan2(R,u*_);m=Math.sin(m*C)/R,a=Math.sin(a*C)/R}const M=a*_;if(l=l*m+f*M,c=c*m+p*M,d=d*m+g*M,h=h*m+x*M,m===1-a){const R=1/Math.sqrt(l*l+c*c+d*d+h*h);l*=R,c*=R,d*=R,h*=R}}e[n]=l,e[n+1]=c,e[n+2]=d,e[n+3]=h}static multiplyQuaternionsFlat(e,n,i,r,s,o){const a=i[r],l=i[r+1],c=i[r+2],d=i[r+3],h=s[o],f=s[o+1],p=s[o+2],g=s[o+3];return e[n]=a*g+d*h+l*p-c*f,e[n+1]=l*g+d*f+c*h-a*p,e[n+2]=c*g+d*p+a*f-l*h,e[n+3]=d*g-a*h-l*f-c*p,e}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get w(){return this._w}set w(e){this._w=e,this._onChangeCallback()}set(e,n,i,r){return this._x=e,this._y=n,this._z=i,this._w=r,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(e){return this._x=e.x,this._y=e.y,this._z=e.z,this._w=e.w,this._onChangeCallback(),this}setFromEuler(e,n=!0){const i=e._x,r=e._y,s=e._z,o=e._order,a=Math.cos,l=Math.sin,c=a(i/2),d=a(r/2),h=a(s/2),f=l(i/2),p=l(r/2),g=l(s/2);switch(o){case"XYZ":this._x=f*d*h+c*p*g,this._y=c*p*h-f*d*g,this._z=c*d*g+f*p*h,this._w=c*d*h-f*p*g;break;case"YXZ":this._x=f*d*h+c*p*g,this._y=c*p*h-f*d*g,this._z=c*d*g-f*p*h,this._w=c*d*h+f*p*g;break;case"ZXY":this._x=f*d*h-c*p*g,this._y=c*p*h+f*d*g,this._z=c*d*g+f*p*h,this._w=c*d*h-f*p*g;break;case"ZYX":this._x=f*d*h-c*p*g,this._y=c*p*h+f*d*g,this._z=c*d*g-f*p*h,this._w=c*d*h+f*p*g;break;case"YZX":this._x=f*d*h+c*p*g,this._y=c*p*h+f*d*g,this._z=c*d*g-f*p*h,this._w=c*d*h-f*p*g;break;case"XZY":this._x=f*d*h-c*p*g,this._y=c*p*h-f*d*g,this._z=c*d*g+f*p*h,this._w=c*d*h+f*p*g;break;default:console.warn("THREE.Quaternion: .setFromEuler() encountered an unknown order: "+o)}return n===!0&&this._onChangeCallback(),this}setFromAxisAngle(e,n){const i=n/2,r=Math.sin(i);return this._x=e.x*r,this._y=e.y*r,this._z=e.z*r,this._w=Math.cos(i),this._onChangeCallback(),this}setFromRotationMatrix(e){const n=e.elements,i=n[0],r=n[4],s=n[8],o=n[1],a=n[5],l=n[9],c=n[2],d=n[6],h=n[10],f=i+a+h;if(f>0){const p=.5/Math.sqrt(f+1);this._w=.25/p,this._x=(d-l)*p,this._y=(s-c)*p,this._z=(o-r)*p}else if(i>a&&i>h){const p=2*Math.sqrt(1+i-a-h);this._w=(d-l)/p,this._x=.25*p,this._y=(r+o)/p,this._z=(s+c)/p}else if(a>h){const p=2*Math.sqrt(1+a-i-h);this._w=(s-c)/p,this._x=(r+o)/p,this._y=.25*p,this._z=(l+d)/p}else{const p=2*Math.sqrt(1+h-i-a);this._w=(o-r)/p,this._x=(s+c)/p,this._y=(l+d)/p,this._z=.25*p}return this._onChangeCallback(),this}setFromUnitVectors(e,n){let i=e.dot(n)+1;return i<Number.EPSILON?(i=0,Math.abs(e.x)>Math.abs(e.z)?(this._x=-e.y,this._y=e.x,this._z=0,this._w=i):(this._x=0,this._y=-e.z,this._z=e.y,this._w=i)):(this._x=e.y*n.z-e.z*n.y,this._y=e.z*n.x-e.x*n.z,this._z=e.x*n.y-e.y*n.x,this._w=i),this.normalize()}angleTo(e){return 2*Math.acos(Math.abs(et(this.dot(e),-1,1)))}rotateTowards(e,n){const i=this.angleTo(e);if(i===0)return this;const r=Math.min(1,n/i);return this.slerp(e,r),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(e){return this._x*e._x+this._y*e._y+this._z*e._z+this._w*e._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let e=this.length();return e===0?(this._x=0,this._y=0,this._z=0,this._w=1):(e=1/e,this._x=this._x*e,this._y=this._y*e,this._z=this._z*e,this._w=this._w*e),this._onChangeCallback(),this}multiply(e){return this.multiplyQuaternions(this,e)}premultiply(e){return this.multiplyQuaternions(e,this)}multiplyQuaternions(e,n){const i=e._x,r=e._y,s=e._z,o=e._w,a=n._x,l=n._y,c=n._z,d=n._w;return this._x=i*d+o*a+r*c-s*l,this._y=r*d+o*l+s*a-i*c,this._z=s*d+o*c+i*l-r*a,this._w=o*d-i*a-r*l-s*c,this._onChangeCallback(),this}slerp(e,n){if(n===0)return this;if(n===1)return this.copy(e);const i=this._x,r=this._y,s=this._z,o=this._w;let a=o*e._w+i*e._x+r*e._y+s*e._z;if(a<0?(this._w=-e._w,this._x=-e._x,this._y=-e._y,this._z=-e._z,a=-a):this.copy(e),a>=1)return this._w=o,this._x=i,this._y=r,this._z=s,this;const l=1-a*a;if(l<=Number.EPSILON){const p=1-n;return this._w=p*o+n*this._w,this._x=p*i+n*this._x,this._y=p*r+n*this._y,this._z=p*s+n*this._z,this.normalize(),this}const c=Math.sqrt(l),d=Math.atan2(c,a),h=Math.sin((1-n)*d)/c,f=Math.sin(n*d)/c;return this._w=o*h+this._w*f,this._x=i*h+this._x*f,this._y=r*h+this._y*f,this._z=s*h+this._z*f,this._onChangeCallback(),this}slerpQuaternions(e,n,i){return this.copy(e).slerp(n,i)}random(){const e=2*Math.PI*Math.random(),n=2*Math.PI*Math.random(),i=Math.random(),r=Math.sqrt(1-i),s=Math.sqrt(i);return this.set(r*Math.sin(e),r*Math.cos(e),s*Math.sin(n),s*Math.cos(n))}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._w===this._w}fromArray(e,n=0){return this._x=e[n],this._y=e[n+1],this._z=e[n+2],this._w=e[n+3],this._onChangeCallback(),this}toArray(e=[],n=0){return e[n]=this._x,e[n+1]=this._y,e[n+2]=this._z,e[n+3]=this._w,e}fromBufferAttribute(e,n){return this._x=e.getX(n),this._y=e.getY(n),this._z=e.getZ(n),this._w=e.getW(n),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}}class O{constructor(e=0,n=0,i=0){O.prototype.isVector3=!0,this.x=e,this.y=n,this.z=i}set(e,n,i){return i===void 0&&(i=this.z),this.x=e,this.y=n,this.z=i,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setComponent(e,n){switch(e){case 0:this.x=n;break;case 1:this.y=n;break;case 2:this.z=n;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this}addVectors(e,n){return this.x=e.x+n.x,this.y=e.y+n.y,this.z=e.z+n.z,this}addScaledVector(e,n){return this.x+=e.x*n,this.y+=e.y*n,this.z+=e.z*n,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this}subVectors(e,n){return this.x=e.x-n.x,this.y=e.y-n.y,this.z=e.z-n.z,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this}multiplyVectors(e,n){return this.x=e.x*n.x,this.y=e.y*n.y,this.z=e.z*n.z,this}applyEuler(e){return this.applyQuaternion(tm.setFromEuler(e))}applyAxisAngle(e,n){return this.applyQuaternion(tm.setFromAxisAngle(e,n))}applyMatrix3(e){const n=this.x,i=this.y,r=this.z,s=e.elements;return this.x=s[0]*n+s[3]*i+s[6]*r,this.y=s[1]*n+s[4]*i+s[7]*r,this.z=s[2]*n+s[5]*i+s[8]*r,this}applyNormalMatrix(e){return this.applyMatrix3(e).normalize()}applyMatrix4(e){const n=this.x,i=this.y,r=this.z,s=e.elements,o=1/(s[3]*n+s[7]*i+s[11]*r+s[15]);return this.x=(s[0]*n+s[4]*i+s[8]*r+s[12])*o,this.y=(s[1]*n+s[5]*i+s[9]*r+s[13])*o,this.z=(s[2]*n+s[6]*i+s[10]*r+s[14])*o,this}applyQuaternion(e){const n=this.x,i=this.y,r=this.z,s=e.x,o=e.y,a=e.z,l=e.w,c=2*(o*r-a*i),d=2*(a*n-s*r),h=2*(s*i-o*n);return this.x=n+l*c+o*h-a*d,this.y=i+l*d+a*c-s*h,this.z=r+l*h+s*d-o*c,this}project(e){return this.applyMatrix4(e.matrixWorldInverse).applyMatrix4(e.projectionMatrix)}unproject(e){return this.applyMatrix4(e.projectionMatrixInverse).applyMatrix4(e.matrixWorld)}transformDirection(e){const n=this.x,i=this.y,r=this.z,s=e.elements;return this.x=s[0]*n+s[4]*i+s[8]*r,this.y=s[1]*n+s[5]*i+s[9]*r,this.z=s[2]*n+s[6]*i+s[10]*r,this.normalize()}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this}divideScalar(e){return this.multiplyScalar(1/e)}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this}clamp(e,n){return this.x=et(this.x,e.x,n.x),this.y=et(this.y,e.y,n.y),this.z=et(this.z,e.z,n.z),this}clampScalar(e,n){return this.x=et(this.x,e,n),this.y=et(this.y,e,n),this.z=et(this.z,e,n),this}clampLength(e,n){const i=this.length();return this.divideScalar(i||1).multiplyScalar(et(i,e,n))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,n){return this.x+=(e.x-this.x)*n,this.y+=(e.y-this.y)*n,this.z+=(e.z-this.z)*n,this}lerpVectors(e,n,i){return this.x=e.x+(n.x-e.x)*i,this.y=e.y+(n.y-e.y)*i,this.z=e.z+(n.z-e.z)*i,this}cross(e){return this.crossVectors(this,e)}crossVectors(e,n){const i=e.x,r=e.y,s=e.z,o=n.x,a=n.y,l=n.z;return this.x=r*l-s*a,this.y=s*o-i*l,this.z=i*a-r*o,this}projectOnVector(e){const n=e.lengthSq();if(n===0)return this.set(0,0,0);const i=e.dot(this)/n;return this.copy(e).multiplyScalar(i)}projectOnPlane(e){return ou.copy(this).projectOnVector(e),this.sub(ou)}reflect(e){return this.sub(ou.copy(e).multiplyScalar(2*this.dot(e)))}angleTo(e){const n=Math.sqrt(this.lengthSq()*e.lengthSq());if(n===0)return Math.PI/2;const i=this.dot(e)/n;return Math.acos(et(i,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){const n=this.x-e.x,i=this.y-e.y,r=this.z-e.z;return n*n+i*i+r*r}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)+Math.abs(this.z-e.z)}setFromSpherical(e){return this.setFromSphericalCoords(e.radius,e.phi,e.theta)}setFromSphericalCoords(e,n,i){const r=Math.sin(n)*e;return this.x=r*Math.sin(i),this.y=Math.cos(n)*e,this.z=r*Math.cos(i),this}setFromCylindrical(e){return this.setFromCylindricalCoords(e.radius,e.theta,e.y)}setFromCylindricalCoords(e,n,i){return this.x=e*Math.sin(n),this.y=i,this.z=e*Math.cos(n),this}setFromMatrixPosition(e){const n=e.elements;return this.x=n[12],this.y=n[13],this.z=n[14],this}setFromMatrixScale(e){const n=this.setFromMatrixColumn(e,0).length(),i=this.setFromMatrixColumn(e,1).length(),r=this.setFromMatrixColumn(e,2).length();return this.x=n,this.y=i,this.z=r,this}setFromMatrixColumn(e,n){return this.fromArray(e.elements,n*4)}setFromMatrix3Column(e,n){return this.fromArray(e.elements,n*3)}setFromEuler(e){return this.x=e._x,this.y=e._y,this.z=e._z,this}setFromColor(e){return this.x=e.r,this.y=e.g,this.z=e.b,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z}fromArray(e,n=0){return this.x=e[n],this.y=e[n+1],this.z=e[n+2],this}toArray(e=[],n=0){return e[n]=this.x,e[n+1]=this.y,e[n+2]=this.z,e}fromBufferAttribute(e,n){return this.x=e.getX(n),this.y=e.getY(n),this.z=e.getZ(n),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this}randomDirection(){const e=Math.random()*Math.PI*2,n=Math.random()*2-1,i=Math.sqrt(1-n*n);return this.x=i*Math.cos(e),this.y=n,this.z=i*Math.sin(e),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}}const ou=new O,tm=new jr;class la{constructor(e=new O(1/0,1/0,1/0),n=new O(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=e,this.max=n}set(e,n){return this.min.copy(e),this.max.copy(n),this}setFromArray(e){this.makeEmpty();for(let n=0,i=e.length;n<i;n+=3)this.expandByPoint(Wn.fromArray(e,n));return this}setFromBufferAttribute(e){this.makeEmpty();for(let n=0,i=e.count;n<i;n++)this.expandByPoint(Wn.fromBufferAttribute(e,n));return this}setFromPoints(e){this.makeEmpty();for(let n=0,i=e.length;n<i;n++)this.expandByPoint(e[n]);return this}setFromCenterAndSize(e,n){const i=Wn.copy(n).multiplyScalar(.5);return this.min.copy(e).sub(i),this.max.copy(e).add(i),this}setFromObject(e,n=!1){return this.makeEmpty(),this.expandByObject(e,n)}clone(){return new this.constructor().copy(this)}copy(e){return this.min.copy(e.min),this.max.copy(e.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(e){return this.isEmpty()?e.set(0,0,0):e.addVectors(this.min,this.max).multiplyScalar(.5)}getSize(e){return this.isEmpty()?e.set(0,0,0):e.subVectors(this.max,this.min)}expandByPoint(e){return this.min.min(e),this.max.max(e),this}expandByVector(e){return this.min.sub(e),this.max.add(e),this}expandByScalar(e){return this.min.addScalar(-e),this.max.addScalar(e),this}expandByObject(e,n=!1){e.updateWorldMatrix(!1,!1);const i=e.geometry;if(i!==void 0){const s=i.getAttribute("position");if(n===!0&&s!==void 0&&e.isInstancedMesh!==!0)for(let o=0,a=s.count;o<a;o++)e.isMesh===!0?e.getVertexPosition(o,Wn):Wn.fromBufferAttribute(s,o),Wn.applyMatrix4(e.matrixWorld),this.expandByPoint(Wn);else e.boundingBox!==void 0?(e.boundingBox===null&&e.computeBoundingBox(),Na.copy(e.boundingBox)):(i.boundingBox===null&&i.computeBoundingBox(),Na.copy(i.boundingBox)),Na.applyMatrix4(e.matrixWorld),this.union(Na)}const r=e.children;for(let s=0,o=r.length;s<o;s++)this.expandByObject(r[s],n);return this}containsPoint(e){return e.x>=this.min.x&&e.x<=this.max.x&&e.y>=this.min.y&&e.y<=this.max.y&&e.z>=this.min.z&&e.z<=this.max.z}containsBox(e){return this.min.x<=e.min.x&&e.max.x<=this.max.x&&this.min.y<=e.min.y&&e.max.y<=this.max.y&&this.min.z<=e.min.z&&e.max.z<=this.max.z}getParameter(e,n){return n.set((e.x-this.min.x)/(this.max.x-this.min.x),(e.y-this.min.y)/(this.max.y-this.min.y),(e.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(e){return e.max.x>=this.min.x&&e.min.x<=this.max.x&&e.max.y>=this.min.y&&e.min.y<=this.max.y&&e.max.z>=this.min.z&&e.min.z<=this.max.z}intersectsSphere(e){return this.clampPoint(e.center,Wn),Wn.distanceToSquared(e.center)<=e.radius*e.radius}intersectsPlane(e){let n,i;return e.normal.x>0?(n=e.normal.x*this.min.x,i=e.normal.x*this.max.x):(n=e.normal.x*this.max.x,i=e.normal.x*this.min.x),e.normal.y>0?(n+=e.normal.y*this.min.y,i+=e.normal.y*this.max.y):(n+=e.normal.y*this.max.y,i+=e.normal.y*this.min.y),e.normal.z>0?(n+=e.normal.z*this.min.z,i+=e.normal.z*this.max.z):(n+=e.normal.z*this.max.z,i+=e.normal.z*this.min.z),n<=-e.constant&&i>=-e.constant}intersectsTriangle(e){if(this.isEmpty())return!1;this.getCenter(fo),Da.subVectors(this.max,fo),Qr.subVectors(e.a,fo),es.subVectors(e.b,fo),ts.subVectors(e.c,fo),zi.subVectors(es,Qr),Hi.subVectors(ts,es),xr.subVectors(Qr,ts);let n=[0,-zi.z,zi.y,0,-Hi.z,Hi.y,0,-xr.z,xr.y,zi.z,0,-zi.x,Hi.z,0,-Hi.x,xr.z,0,-xr.x,-zi.y,zi.x,0,-Hi.y,Hi.x,0,-xr.y,xr.x,0];return!au(n,Qr,es,ts,Da)||(n=[1,0,0,0,1,0,0,0,1],!au(n,Qr,es,ts,Da))?!1:(Ia.crossVectors(zi,Hi),n=[Ia.x,Ia.y,Ia.z],au(n,Qr,es,ts,Da))}clampPoint(e,n){return n.copy(e).clamp(this.min,this.max)}distanceToPoint(e){return this.clampPoint(e,Wn).distanceTo(e)}getBoundingSphere(e){return this.isEmpty()?e.makeEmpty():(this.getCenter(e.center),e.radius=this.getSize(Wn).length()*.5),e}intersect(e){return this.min.max(e.min),this.max.min(e.max),this.isEmpty()&&this.makeEmpty(),this}union(e){return this.min.min(e.min),this.max.max(e.max),this}applyMatrix4(e){return this.isEmpty()?this:(gi[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(e),gi[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(e),gi[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(e),gi[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(e),gi[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(e),gi[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(e),gi[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(e),gi[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(e),this.setFromPoints(gi),this)}translate(e){return this.min.add(e),this.max.add(e),this}equals(e){return e.min.equals(this.min)&&e.max.equals(this.max)}}const gi=[new O,new O,new O,new O,new O,new O,new O,new O],Wn=new O,Na=new la,Qr=new O,es=new O,ts=new O,zi=new O,Hi=new O,xr=new O,fo=new O,Da=new O,Ia=new O,yr=new O;function au(t,e,n,i,r){for(let s=0,o=t.length-3;s<=o;s+=3){yr.fromArray(t,s);const a=r.x*Math.abs(yr.x)+r.y*Math.abs(yr.y)+r.z*Math.abs(yr.z),l=e.dot(yr),c=n.dot(yr),d=i.dot(yr);if(Math.max(-Math.max(l,c,d),Math.min(l,c,d))>a)return!1}return!0}const tM=new la,po=new O,lu=new O;class Sc{constructor(e=new O,n=-1){this.isSphere=!0,this.center=e,this.radius=n}set(e,n){return this.center.copy(e),this.radius=n,this}setFromPoints(e,n){const i=this.center;n!==void 0?i.copy(n):tM.setFromPoints(e).getCenter(i);let r=0;for(let s=0,o=e.length;s<o;s++)r=Math.max(r,i.distanceToSquared(e[s]));return this.radius=Math.sqrt(r),this}copy(e){return this.center.copy(e.center),this.radius=e.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(e){return e.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(e){return e.distanceTo(this.center)-this.radius}intersectsSphere(e){const n=this.radius+e.radius;return e.center.distanceToSquared(this.center)<=n*n}intersectsBox(e){return e.intersectsSphere(this)}intersectsPlane(e){return Math.abs(e.distanceToPoint(this.center))<=this.radius}clampPoint(e,n){const i=this.center.distanceToSquared(e);return n.copy(e),i>this.radius*this.radius&&(n.sub(this.center).normalize(),n.multiplyScalar(this.radius).add(this.center)),n}getBoundingBox(e){return this.isEmpty()?(e.makeEmpty(),e):(e.set(this.center,this.center),e.expandByScalar(this.radius),e)}applyMatrix4(e){return this.center.applyMatrix4(e),this.radius=this.radius*e.getMaxScaleOnAxis(),this}translate(e){return this.center.add(e),this}expandByPoint(e){if(this.isEmpty())return this.center.copy(e),this.radius=0,this;po.subVectors(e,this.center);const n=po.lengthSq();if(n>this.radius*this.radius){const i=Math.sqrt(n),r=(i-this.radius)*.5;this.center.addScaledVector(po,r/i),this.radius+=r}return this}union(e){return e.isEmpty()?this:this.isEmpty()?(this.copy(e),this):(this.center.equals(e.center)===!0?this.radius=Math.max(this.radius,e.radius):(lu.subVectors(e.center,this.center).setLength(e.radius),this.expandByPoint(po.copy(e.center).add(lu)),this.expandByPoint(po.copy(e.center).sub(lu))),this)}equals(e){return e.center.equals(this.center)&&e.radius===this.radius}clone(){return new this.constructor().copy(this)}}const _i=new O,cu=new O,Ua=new O,Vi=new O,uu=new O,Oa=new O,du=new O;class Mc{constructor(e=new O,n=new O(0,0,-1)){this.origin=e,this.direction=n}set(e,n){return this.origin.copy(e),this.direction.copy(n),this}copy(e){return this.origin.copy(e.origin),this.direction.copy(e.direction),this}at(e,n){return n.copy(this.origin).addScaledVector(this.direction,e)}lookAt(e){return this.direction.copy(e).sub(this.origin).normalize(),this}recast(e){return this.origin.copy(this.at(e,_i)),this}closestPointToPoint(e,n){n.subVectors(e,this.origin);const i=n.dot(this.direction);return i<0?n.copy(this.origin):n.copy(this.origin).addScaledVector(this.direction,i)}distanceToPoint(e){return Math.sqrt(this.distanceSqToPoint(e))}distanceSqToPoint(e){const n=_i.subVectors(e,this.origin).dot(this.direction);return n<0?this.origin.distanceToSquared(e):(_i.copy(this.origin).addScaledVector(this.direction,n),_i.distanceToSquared(e))}distanceSqToSegment(e,n,i,r){cu.copy(e).add(n).multiplyScalar(.5),Ua.copy(n).sub(e).normalize(),Vi.copy(this.origin).sub(cu);const s=e.distanceTo(n)*.5,o=-this.direction.dot(Ua),a=Vi.dot(this.direction),l=-Vi.dot(Ua),c=Vi.lengthSq(),d=Math.abs(1-o*o);let h,f,p,g;if(d>0)if(h=o*l-a,f=o*a-l,g=s*d,h>=0)if(f>=-g)if(f<=g){const x=1/d;h*=x,f*=x,p=h*(h+o*f+2*a)+f*(o*h+f+2*l)+c}else f=s,h=Math.max(0,-(o*f+a)),p=-h*h+f*(f+2*l)+c;else f=-s,h=Math.max(0,-(o*f+a)),p=-h*h+f*(f+2*l)+c;else f<=-g?(h=Math.max(0,-(-o*s+a)),f=h>0?-s:Math.min(Math.max(-s,-l),s),p=-h*h+f*(f+2*l)+c):f<=g?(h=0,f=Math.min(Math.max(-s,-l),s),p=f*(f+2*l)+c):(h=Math.max(0,-(o*s+a)),f=h>0?s:Math.min(Math.max(-s,-l),s),p=-h*h+f*(f+2*l)+c);else f=o>0?-s:s,h=Math.max(0,-(o*f+a)),p=-h*h+f*(f+2*l)+c;return i&&i.copy(this.origin).addScaledVector(this.direction,h),r&&r.copy(cu).addScaledVector(Ua,f),p}intersectSphere(e,n){_i.subVectors(e.center,this.origin);const i=_i.dot(this.direction),r=_i.dot(_i)-i*i,s=e.radius*e.radius;if(r>s)return null;const o=Math.sqrt(s-r),a=i-o,l=i+o;return l<0?null:a<0?this.at(l,n):this.at(a,n)}intersectsSphere(e){return this.distanceSqToPoint(e.center)<=e.radius*e.radius}distanceToPlane(e){const n=e.normal.dot(this.direction);if(n===0)return e.distanceToPoint(this.origin)===0?0:null;const i=-(this.origin.dot(e.normal)+e.constant)/n;return i>=0?i:null}intersectPlane(e,n){const i=this.distanceToPlane(e);return i===null?null:this.at(i,n)}intersectsPlane(e){const n=e.distanceToPoint(this.origin);return n===0||e.normal.dot(this.direction)*n<0}intersectBox(e,n){let i,r,s,o,a,l;const c=1/this.direction.x,d=1/this.direction.y,h=1/this.direction.z,f=this.origin;return c>=0?(i=(e.min.x-f.x)*c,r=(e.max.x-f.x)*c):(i=(e.max.x-f.x)*c,r=(e.min.x-f.x)*c),d>=0?(s=(e.min.y-f.y)*d,o=(e.max.y-f.y)*d):(s=(e.max.y-f.y)*d,o=(e.min.y-f.y)*d),i>o||s>r||((s>i||isNaN(i))&&(i=s),(o<r||isNaN(r))&&(r=o),h>=0?(a=(e.min.z-f.z)*h,l=(e.max.z-f.z)*h):(a=(e.max.z-f.z)*h,l=(e.min.z-f.z)*h),i>l||a>r)||((a>i||i!==i)&&(i=a),(l<r||r!==r)&&(r=l),r<0)?null:this.at(i>=0?i:r,n)}intersectsBox(e){return this.intersectBox(e,_i)!==null}intersectTriangle(e,n,i,r,s){uu.subVectors(n,e),Oa.subVectors(i,e),du.crossVectors(uu,Oa);let o=this.direction.dot(du),a;if(o>0){if(r)return null;a=1}else if(o<0)a=-1,o=-o;else return null;Vi.subVectors(this.origin,e);const l=a*this.direction.dot(Oa.crossVectors(Vi,Oa));if(l<0)return null;const c=a*this.direction.dot(uu.cross(Vi));if(c<0||l+c>o)return null;const d=-a*Vi.dot(du);return d<0?null:this.at(d/o,s)}applyMatrix4(e){return this.origin.applyMatrix4(e),this.direction.transformDirection(e),this}equals(e){return e.origin.equals(this.origin)&&e.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}}class mt{constructor(e,n,i,r,s,o,a,l,c,d,h,f,p,g,x,m){mt.prototype.isMatrix4=!0,this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],e!==void 0&&this.set(e,n,i,r,s,o,a,l,c,d,h,f,p,g,x,m)}set(e,n,i,r,s,o,a,l,c,d,h,f,p,g,x,m){const u=this.elements;return u[0]=e,u[4]=n,u[8]=i,u[12]=r,u[1]=s,u[5]=o,u[9]=a,u[13]=l,u[2]=c,u[6]=d,u[10]=h,u[14]=f,u[3]=p,u[7]=g,u[11]=x,u[15]=m,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new mt().fromArray(this.elements)}copy(e){const n=this.elements,i=e.elements;return n[0]=i[0],n[1]=i[1],n[2]=i[2],n[3]=i[3],n[4]=i[4],n[5]=i[5],n[6]=i[6],n[7]=i[7],n[8]=i[8],n[9]=i[9],n[10]=i[10],n[11]=i[11],n[12]=i[12],n[13]=i[13],n[14]=i[14],n[15]=i[15],this}copyPosition(e){const n=this.elements,i=e.elements;return n[12]=i[12],n[13]=i[13],n[14]=i[14],this}setFromMatrix3(e){const n=e.elements;return this.set(n[0],n[3],n[6],0,n[1],n[4],n[7],0,n[2],n[5],n[8],0,0,0,0,1),this}extractBasis(e,n,i){return e.setFromMatrixColumn(this,0),n.setFromMatrixColumn(this,1),i.setFromMatrixColumn(this,2),this}makeBasis(e,n,i){return this.set(e.x,n.x,i.x,0,e.y,n.y,i.y,0,e.z,n.z,i.z,0,0,0,0,1),this}extractRotation(e){const n=this.elements,i=e.elements,r=1/ns.setFromMatrixColumn(e,0).length(),s=1/ns.setFromMatrixColumn(e,1).length(),o=1/ns.setFromMatrixColumn(e,2).length();return n[0]=i[0]*r,n[1]=i[1]*r,n[2]=i[2]*r,n[3]=0,n[4]=i[4]*s,n[5]=i[5]*s,n[6]=i[6]*s,n[7]=0,n[8]=i[8]*o,n[9]=i[9]*o,n[10]=i[10]*o,n[11]=0,n[12]=0,n[13]=0,n[14]=0,n[15]=1,this}makeRotationFromEuler(e){const n=this.elements,i=e.x,r=e.y,s=e.z,o=Math.cos(i),a=Math.sin(i),l=Math.cos(r),c=Math.sin(r),d=Math.cos(s),h=Math.sin(s);if(e.order==="XYZ"){const f=o*d,p=o*h,g=a*d,x=a*h;n[0]=l*d,n[4]=-l*h,n[8]=c,n[1]=p+g*c,n[5]=f-x*c,n[9]=-a*l,n[2]=x-f*c,n[6]=g+p*c,n[10]=o*l}else if(e.order==="YXZ"){const f=l*d,p=l*h,g=c*d,x=c*h;n[0]=f+x*a,n[4]=g*a-p,n[8]=o*c,n[1]=o*h,n[5]=o*d,n[9]=-a,n[2]=p*a-g,n[6]=x+f*a,n[10]=o*l}else if(e.order==="ZXY"){const f=l*d,p=l*h,g=c*d,x=c*h;n[0]=f-x*a,n[4]=-o*h,n[8]=g+p*a,n[1]=p+g*a,n[5]=o*d,n[9]=x-f*a,n[2]=-o*c,n[6]=a,n[10]=o*l}else if(e.order==="ZYX"){const f=o*d,p=o*h,g=a*d,x=a*h;n[0]=l*d,n[4]=g*c-p,n[8]=f*c+x,n[1]=l*h,n[5]=x*c+f,n[9]=p*c-g,n[2]=-c,n[6]=a*l,n[10]=o*l}else if(e.order==="YZX"){const f=o*l,p=o*c,g=a*l,x=a*c;n[0]=l*d,n[4]=x-f*h,n[8]=g*h+p,n[1]=h,n[5]=o*d,n[9]=-a*d,n[2]=-c*d,n[6]=p*h+g,n[10]=f-x*h}else if(e.order==="XZY"){const f=o*l,p=o*c,g=a*l,x=a*c;n[0]=l*d,n[4]=-h,n[8]=c*d,n[1]=f*h+x,n[5]=o*d,n[9]=p*h-g,n[2]=g*h-p,n[6]=a*d,n[10]=x*h+f}return n[3]=0,n[7]=0,n[11]=0,n[12]=0,n[13]=0,n[14]=0,n[15]=1,this}makeRotationFromQuaternion(e){return this.compose(nM,e,iM)}lookAt(e,n,i){const r=this.elements;return Sn.subVectors(e,n),Sn.lengthSq()===0&&(Sn.z=1),Sn.normalize(),Gi.crossVectors(i,Sn),Gi.lengthSq()===0&&(Math.abs(i.z)===1?Sn.x+=1e-4:Sn.z+=1e-4,Sn.normalize(),Gi.crossVectors(i,Sn)),Gi.normalize(),Fa.crossVectors(Sn,Gi),r[0]=Gi.x,r[4]=Fa.x,r[8]=Sn.x,r[1]=Gi.y,r[5]=Fa.y,r[9]=Sn.y,r[2]=Gi.z,r[6]=Fa.z,r[10]=Sn.z,this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,n){const i=e.elements,r=n.elements,s=this.elements,o=i[0],a=i[4],l=i[8],c=i[12],d=i[1],h=i[5],f=i[9],p=i[13],g=i[2],x=i[6],m=i[10],u=i[14],_=i[3],v=i[7],M=i[11],R=i[15],C=r[0],A=r[4],P=r[8],E=r[12],S=r[1],D=r[5],X=r[9],H=r[13],U=r[2],Y=r[6],V=r[10],J=r[14],N=r[3],j=r[7],Z=r[11],fe=r[15];return s[0]=o*C+a*S+l*U+c*N,s[4]=o*A+a*D+l*Y+c*j,s[8]=o*P+a*X+l*V+c*Z,s[12]=o*E+a*H+l*J+c*fe,s[1]=d*C+h*S+f*U+p*N,s[5]=d*A+h*D+f*Y+p*j,s[9]=d*P+h*X+f*V+p*Z,s[13]=d*E+h*H+f*J+p*fe,s[2]=g*C+x*S+m*U+u*N,s[6]=g*A+x*D+m*Y+u*j,s[10]=g*P+x*X+m*V+u*Z,s[14]=g*E+x*H+m*J+u*fe,s[3]=_*C+v*S+M*U+R*N,s[7]=_*A+v*D+M*Y+R*j,s[11]=_*P+v*X+M*V+R*Z,s[15]=_*E+v*H+M*J+R*fe,this}multiplyScalar(e){const n=this.elements;return n[0]*=e,n[4]*=e,n[8]*=e,n[12]*=e,n[1]*=e,n[5]*=e,n[9]*=e,n[13]*=e,n[2]*=e,n[6]*=e,n[10]*=e,n[14]*=e,n[3]*=e,n[7]*=e,n[11]*=e,n[15]*=e,this}determinant(){const e=this.elements,n=e[0],i=e[4],r=e[8],s=e[12],o=e[1],a=e[5],l=e[9],c=e[13],d=e[2],h=e[6],f=e[10],p=e[14],g=e[3],x=e[7],m=e[11],u=e[15];return g*(+s*l*h-r*c*h-s*a*f+i*c*f+r*a*p-i*l*p)+x*(+n*l*p-n*c*f+s*o*f-r*o*p+r*c*d-s*l*d)+m*(+n*c*h-n*a*p-s*o*h+i*o*p+s*a*d-i*c*d)+u*(-r*a*d-n*l*h+n*a*f+r*o*h-i*o*f+i*l*d)}transpose(){const e=this.elements;let n;return n=e[1],e[1]=e[4],e[4]=n,n=e[2],e[2]=e[8],e[8]=n,n=e[6],e[6]=e[9],e[9]=n,n=e[3],e[3]=e[12],e[12]=n,n=e[7],e[7]=e[13],e[13]=n,n=e[11],e[11]=e[14],e[14]=n,this}setPosition(e,n,i){const r=this.elements;return e.isVector3?(r[12]=e.x,r[13]=e.y,r[14]=e.z):(r[12]=e,r[13]=n,r[14]=i),this}invert(){const e=this.elements,n=e[0],i=e[1],r=e[2],s=e[3],o=e[4],a=e[5],l=e[6],c=e[7],d=e[8],h=e[9],f=e[10],p=e[11],g=e[12],x=e[13],m=e[14],u=e[15],_=h*m*c-x*f*c+x*l*p-a*m*p-h*l*u+a*f*u,v=g*f*c-d*m*c-g*l*p+o*m*p+d*l*u-o*f*u,M=d*x*c-g*h*c+g*a*p-o*x*p-d*a*u+o*h*u,R=g*h*l-d*x*l-g*a*f+o*x*f+d*a*m-o*h*m,C=n*_+i*v+r*M+s*R;if(C===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);const A=1/C;return e[0]=_*A,e[1]=(x*f*s-h*m*s-x*r*p+i*m*p+h*r*u-i*f*u)*A,e[2]=(a*m*s-x*l*s+x*r*c-i*m*c-a*r*u+i*l*u)*A,e[3]=(h*l*s-a*f*s-h*r*c+i*f*c+a*r*p-i*l*p)*A,e[4]=v*A,e[5]=(d*m*s-g*f*s+g*r*p-n*m*p-d*r*u+n*f*u)*A,e[6]=(g*l*s-o*m*s-g*r*c+n*m*c+o*r*u-n*l*u)*A,e[7]=(o*f*s-d*l*s+d*r*c-n*f*c-o*r*p+n*l*p)*A,e[8]=M*A,e[9]=(g*h*s-d*x*s-g*i*p+n*x*p+d*i*u-n*h*u)*A,e[10]=(o*x*s-g*a*s+g*i*c-n*x*c-o*i*u+n*a*u)*A,e[11]=(d*a*s-o*h*s-d*i*c+n*h*c+o*i*p-n*a*p)*A,e[12]=R*A,e[13]=(d*x*r-g*h*r+g*i*f-n*x*f-d*i*m+n*h*m)*A,e[14]=(g*a*r-o*x*r-g*i*l+n*x*l+o*i*m-n*a*m)*A,e[15]=(o*h*r-d*a*r+d*i*l-n*h*l-o*i*f+n*a*f)*A,this}scale(e){const n=this.elements,i=e.x,r=e.y,s=e.z;return n[0]*=i,n[4]*=r,n[8]*=s,n[1]*=i,n[5]*=r,n[9]*=s,n[2]*=i,n[6]*=r,n[10]*=s,n[3]*=i,n[7]*=r,n[11]*=s,this}getMaxScaleOnAxis(){const e=this.elements,n=e[0]*e[0]+e[1]*e[1]+e[2]*e[2],i=e[4]*e[4]+e[5]*e[5]+e[6]*e[6],r=e[8]*e[8]+e[9]*e[9]+e[10]*e[10];return Math.sqrt(Math.max(n,i,r))}makeTranslation(e,n,i){return e.isVector3?this.set(1,0,0,e.x,0,1,0,e.y,0,0,1,e.z,0,0,0,1):this.set(1,0,0,e,0,1,0,n,0,0,1,i,0,0,0,1),this}makeRotationX(e){const n=Math.cos(e),i=Math.sin(e);return this.set(1,0,0,0,0,n,-i,0,0,i,n,0,0,0,0,1),this}makeRotationY(e){const n=Math.cos(e),i=Math.sin(e);return this.set(n,0,i,0,0,1,0,0,-i,0,n,0,0,0,0,1),this}makeRotationZ(e){const n=Math.cos(e),i=Math.sin(e);return this.set(n,-i,0,0,i,n,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(e,n){const i=Math.cos(n),r=Math.sin(n),s=1-i,o=e.x,a=e.y,l=e.z,c=s*o,d=s*a;return this.set(c*o+i,c*a-r*l,c*l+r*a,0,c*a+r*l,d*a+i,d*l-r*o,0,c*l-r*a,d*l+r*o,s*l*l+i,0,0,0,0,1),this}makeScale(e,n,i){return this.set(e,0,0,0,0,n,0,0,0,0,i,0,0,0,0,1),this}makeShear(e,n,i,r,s,o){return this.set(1,i,s,0,e,1,o,0,n,r,1,0,0,0,0,1),this}compose(e,n,i){const r=this.elements,s=n._x,o=n._y,a=n._z,l=n._w,c=s+s,d=o+o,h=a+a,f=s*c,p=s*d,g=s*h,x=o*d,m=o*h,u=a*h,_=l*c,v=l*d,M=l*h,R=i.x,C=i.y,A=i.z;return r[0]=(1-(x+u))*R,r[1]=(p+M)*R,r[2]=(g-v)*R,r[3]=0,r[4]=(p-M)*C,r[5]=(1-(f+u))*C,r[6]=(m+_)*C,r[7]=0,r[8]=(g+v)*A,r[9]=(m-_)*A,r[10]=(1-(f+x))*A,r[11]=0,r[12]=e.x,r[13]=e.y,r[14]=e.z,r[15]=1,this}decompose(e,n,i){const r=this.elements;let s=ns.set(r[0],r[1],r[2]).length();const o=ns.set(r[4],r[5],r[6]).length(),a=ns.set(r[8],r[9],r[10]).length();this.determinant()<0&&(s=-s),e.x=r[12],e.y=r[13],e.z=r[14],Xn.copy(this);const c=1/s,d=1/o,h=1/a;return Xn.elements[0]*=c,Xn.elements[1]*=c,Xn.elements[2]*=c,Xn.elements[4]*=d,Xn.elements[5]*=d,Xn.elements[6]*=d,Xn.elements[8]*=h,Xn.elements[9]*=h,Xn.elements[10]*=h,n.setFromRotationMatrix(Xn),i.x=s,i.y=o,i.z=a,this}makePerspective(e,n,i,r,s,o,a=bi){const l=this.elements,c=2*s/(n-e),d=2*s/(i-r),h=(n+e)/(n-e),f=(i+r)/(i-r);let p,g;if(a===bi)p=-(o+s)/(o-s),g=-2*o*s/(o-s);else if(a===Zl)p=-o/(o-s),g=-o*s/(o-s);else throw new Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+a);return l[0]=c,l[4]=0,l[8]=h,l[12]=0,l[1]=0,l[5]=d,l[9]=f,l[13]=0,l[2]=0,l[6]=0,l[10]=p,l[14]=g,l[3]=0,l[7]=0,l[11]=-1,l[15]=0,this}makeOrthographic(e,n,i,r,s,o,a=bi){const l=this.elements,c=1/(n-e),d=1/(i-r),h=1/(o-s),f=(n+e)*c,p=(i+r)*d;let g,x;if(a===bi)g=(o+s)*h,x=-2*h;else if(a===Zl)g=s*h,x=-1*h;else throw new Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+a);return l[0]=2*c,l[4]=0,l[8]=0,l[12]=-f,l[1]=0,l[5]=2*d,l[9]=0,l[13]=-p,l[2]=0,l[6]=0,l[10]=x,l[14]=-g,l[3]=0,l[7]=0,l[11]=0,l[15]=1,this}equals(e){const n=this.elements,i=e.elements;for(let r=0;r<16;r++)if(n[r]!==i[r])return!1;return!0}fromArray(e,n=0){for(let i=0;i<16;i++)this.elements[i]=e[i+n];return this}toArray(e=[],n=0){const i=this.elements;return e[n]=i[0],e[n+1]=i[1],e[n+2]=i[2],e[n+3]=i[3],e[n+4]=i[4],e[n+5]=i[5],e[n+6]=i[6],e[n+7]=i[7],e[n+8]=i[8],e[n+9]=i[9],e[n+10]=i[10],e[n+11]=i[11],e[n+12]=i[12],e[n+13]=i[13],e[n+14]=i[14],e[n+15]=i[15],e}}const ns=new O,Xn=new mt,nM=new O(0,0,0),iM=new O(1,1,1),Gi=new O,Fa=new O,Sn=new O,nm=new mt,im=new jr;class hi{constructor(e=0,n=0,i=0,r=hi.DEFAULT_ORDER){this.isEuler=!0,this._x=e,this._y=n,this._z=i,this._order=r}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get order(){return this._order}set order(e){this._order=e,this._onChangeCallback()}set(e,n,i,r=this._order){return this._x=e,this._y=n,this._z=i,this._order=r,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(e){return this._x=e._x,this._y=e._y,this._z=e._z,this._order=e._order,this._onChangeCallback(),this}setFromRotationMatrix(e,n=this._order,i=!0){const r=e.elements,s=r[0],o=r[4],a=r[8],l=r[1],c=r[5],d=r[9],h=r[2],f=r[6],p=r[10];switch(n){case"XYZ":this._y=Math.asin(et(a,-1,1)),Math.abs(a)<.9999999?(this._x=Math.atan2(-d,p),this._z=Math.atan2(-o,s)):(this._x=Math.atan2(f,c),this._z=0);break;case"YXZ":this._x=Math.asin(-et(d,-1,1)),Math.abs(d)<.9999999?(this._y=Math.atan2(a,p),this._z=Math.atan2(l,c)):(this._y=Math.atan2(-h,s),this._z=0);break;case"ZXY":this._x=Math.asin(et(f,-1,1)),Math.abs(f)<.9999999?(this._y=Math.atan2(-h,p),this._z=Math.atan2(-o,c)):(this._y=0,this._z=Math.atan2(l,s));break;case"ZYX":this._y=Math.asin(-et(h,-1,1)),Math.abs(h)<.9999999?(this._x=Math.atan2(f,p),this._z=Math.atan2(l,s)):(this._x=0,this._z=Math.atan2(-o,c));break;case"YZX":this._z=Math.asin(et(l,-1,1)),Math.abs(l)<.9999999?(this._x=Math.atan2(-d,c),this._y=Math.atan2(-h,s)):(this._x=0,this._y=Math.atan2(a,p));break;case"XZY":this._z=Math.asin(-et(o,-1,1)),Math.abs(o)<.9999999?(this._x=Math.atan2(f,c),this._y=Math.atan2(a,s)):(this._x=Math.atan2(-d,p),this._y=0);break;default:console.warn("THREE.Euler: .setFromRotationMatrix() encountered an unknown order: "+n)}return this._order=n,i===!0&&this._onChangeCallback(),this}setFromQuaternion(e,n,i){return nm.makeRotationFromQuaternion(e),this.setFromRotationMatrix(nm,n,i)}setFromVector3(e,n=this._order){return this.set(e.x,e.y,e.z,n)}reorder(e){return im.setFromEuler(this),this.setFromQuaternion(im,e)}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._order===this._order}fromArray(e){return this._x=e[0],this._y=e[1],this._z=e[2],e[3]!==void 0&&(this._order=e[3]),this._onChangeCallback(),this}toArray(e=[],n=0){return e[n]=this._x,e[n+1]=this._y,e[n+2]=this._z,e[n+3]=this._order,e}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}}hi.DEFAULT_ORDER="XYZ";class Cf{constructor(){this.mask=1}set(e){this.mask=(1<<e|0)>>>0}enable(e){this.mask|=1<<e|0}enableAll(){this.mask=-1}toggle(e){this.mask^=1<<e|0}disable(e){this.mask&=~(1<<e|0)}disableAll(){this.mask=0}test(e){return(this.mask&e.mask)!==0}isEnabled(e){return(this.mask&(1<<e|0))!==0}}let rM=0;const rm=new O,is=new jr,vi=new mt,ka=new O,mo=new O,sM=new O,oM=new jr,sm=new O(1,0,0),om=new O(0,1,0),am=new O(0,0,1),lm={type:"added"},aM={type:"removed"},rs={type:"childadded",child:null},hu={type:"childremoved",child:null};class kt extends $r{constructor(){super(),this.isObject3D=!0,Object.defineProperty(this,"id",{value:rM++}),this.uuid=aa(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=kt.DEFAULT_UP.clone();const e=new O,n=new hi,i=new jr,r=new O(1,1,1);function s(){i.setFromEuler(n,!1)}function o(){n.setFromQuaternion(i,void 0,!1)}n._onChange(s),i._onChange(o),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:e},rotation:{configurable:!0,enumerable:!0,value:n},quaternion:{configurable:!0,enumerable:!0,value:i},scale:{configurable:!0,enumerable:!0,value:r},modelViewMatrix:{value:new mt},normalMatrix:{value:new Ze}}),this.matrix=new mt,this.matrixWorld=new mt,this.matrixAutoUpdate=kt.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=kt.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new Cf,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.userData={}}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(e){this.matrixAutoUpdate&&this.updateMatrix(),this.matrix.premultiply(e),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(e){return this.quaternion.premultiply(e),this}setRotationFromAxisAngle(e,n){this.quaternion.setFromAxisAngle(e,n)}setRotationFromEuler(e){this.quaternion.setFromEuler(e,!0)}setRotationFromMatrix(e){this.quaternion.setFromRotationMatrix(e)}setRotationFromQuaternion(e){this.quaternion.copy(e)}rotateOnAxis(e,n){return is.setFromAxisAngle(e,n),this.quaternion.multiply(is),this}rotateOnWorldAxis(e,n){return is.setFromAxisAngle(e,n),this.quaternion.premultiply(is),this}rotateX(e){return this.rotateOnAxis(sm,e)}rotateY(e){return this.rotateOnAxis(om,e)}rotateZ(e){return this.rotateOnAxis(am,e)}translateOnAxis(e,n){return rm.copy(e).applyQuaternion(this.quaternion),this.position.add(rm.multiplyScalar(n)),this}translateX(e){return this.translateOnAxis(sm,e)}translateY(e){return this.translateOnAxis(om,e)}translateZ(e){return this.translateOnAxis(am,e)}localToWorld(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(this.matrixWorld)}worldToLocal(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(vi.copy(this.matrixWorld).invert())}lookAt(e,n,i){e.isVector3?ka.copy(e):ka.set(e,n,i);const r=this.parent;this.updateWorldMatrix(!0,!1),mo.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight?vi.lookAt(mo,ka,this.up):vi.lookAt(ka,mo,this.up),this.quaternion.setFromRotationMatrix(vi),r&&(vi.extractRotation(r.matrixWorld),is.setFromRotationMatrix(vi),this.quaternion.premultiply(is.invert()))}add(e){if(arguments.length>1){for(let n=0;n<arguments.length;n++)this.add(arguments[n]);return this}return e===this?(console.error("THREE.Object3D.add: object can't be added as a child of itself.",e),this):(e&&e.isObject3D?(e.removeFromParent(),e.parent=this,this.children.push(e),e.dispatchEvent(lm),rs.child=e,this.dispatchEvent(rs),rs.child=null):console.error("THREE.Object3D.add: object not an instance of THREE.Object3D.",e),this)}remove(e){if(arguments.length>1){for(let i=0;i<arguments.length;i++)this.remove(arguments[i]);return this}const n=this.children.indexOf(e);return n!==-1&&(e.parent=null,this.children.splice(n,1),e.dispatchEvent(aM),hu.child=e,this.dispatchEvent(hu),hu.child=null),this}removeFromParent(){const e=this.parent;return e!==null&&e.remove(this),this}clear(){return this.remove(...this.children)}attach(e){return this.updateWorldMatrix(!0,!1),vi.copy(this.matrixWorld).invert(),e.parent!==null&&(e.parent.updateWorldMatrix(!0,!1),vi.multiply(e.parent.matrixWorld)),e.applyMatrix4(vi),e.removeFromParent(),e.parent=this,this.children.push(e),e.updateWorldMatrix(!1,!0),e.dispatchEvent(lm),rs.child=e,this.dispatchEvent(rs),rs.child=null,this}getObjectById(e){return this.getObjectByProperty("id",e)}getObjectByName(e){return this.getObjectByProperty("name",e)}getObjectByProperty(e,n){if(this[e]===n)return this;for(let i=0,r=this.children.length;i<r;i++){const o=this.children[i].getObjectByProperty(e,n);if(o!==void 0)return o}}getObjectsByProperty(e,n,i=[]){this[e]===n&&i.push(this);const r=this.children;for(let s=0,o=r.length;s<o;s++)r[s].getObjectsByProperty(e,n,i);return i}getWorldPosition(e){return this.updateWorldMatrix(!0,!1),e.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(mo,e,sM),e}getWorldScale(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(mo,oM,e),e}getWorldDirection(e){this.updateWorldMatrix(!0,!1);const n=this.matrixWorld.elements;return e.set(n[8],n[9],n[10]).normalize()}raycast(){}traverse(e){e(this);const n=this.children;for(let i=0,r=n.length;i<r;i++)n[i].traverse(e)}traverseVisible(e){if(this.visible===!1)return;e(this);const n=this.children;for(let i=0,r=n.length;i<r;i++)n[i].traverseVisible(e)}traverseAncestors(e){const n=this.parent;n!==null&&(e(n),n.traverseAncestors(e))}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale),this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(e){this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||e)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,e=!0);const n=this.children;for(let i=0,r=n.length;i<r;i++)n[i].updateMatrixWorld(e)}updateWorldMatrix(e,n){const i=this.parent;if(e===!0&&i!==null&&i.updateWorldMatrix(!0,!1),this.matrixAutoUpdate&&this.updateMatrix(),this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),n===!0){const r=this.children;for(let s=0,o=r.length;s<o;s++)r[s].updateWorldMatrix(!1,!0)}}toJSON(e){const n=e===void 0||typeof e=="string",i={};n&&(e={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},i.metadata={version:4.6,type:"Object",generator:"Object3D.toJSON"});const r={};r.uuid=this.uuid,r.type=this.type,this.name!==""&&(r.name=this.name),this.castShadow===!0&&(r.castShadow=!0),this.receiveShadow===!0&&(r.receiveShadow=!0),this.visible===!1&&(r.visible=!1),this.frustumCulled===!1&&(r.frustumCulled=!1),this.renderOrder!==0&&(r.renderOrder=this.renderOrder),Object.keys(this.userData).length>0&&(r.userData=this.userData),r.layers=this.layers.mask,r.matrix=this.matrix.toArray(),r.up=this.up.toArray(),this.matrixAutoUpdate===!1&&(r.matrixAutoUpdate=!1),this.isInstancedMesh&&(r.type="InstancedMesh",r.count=this.count,r.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null&&(r.instanceColor=this.instanceColor.toJSON())),this.isBatchedMesh&&(r.type="BatchedMesh",r.perObjectFrustumCulled=this.perObjectFrustumCulled,r.sortObjects=this.sortObjects,r.drawRanges=this._drawRanges,r.reservedRanges=this._reservedRanges,r.visibility=this._visibility,r.active=this._active,r.bounds=this._bounds.map(a=>({boxInitialized:a.boxInitialized,boxMin:a.box.min.toArray(),boxMax:a.box.max.toArray(),sphereInitialized:a.sphereInitialized,sphereRadius:a.sphere.radius,sphereCenter:a.sphere.center.toArray()})),r.maxInstanceCount=this._maxInstanceCount,r.maxVertexCount=this._maxVertexCount,r.maxIndexCount=this._maxIndexCount,r.geometryInitialized=this._geometryInitialized,r.geometryCount=this._geometryCount,r.matricesTexture=this._matricesTexture.toJSON(e),this._colorsTexture!==null&&(r.colorsTexture=this._colorsTexture.toJSON(e)),this.boundingSphere!==null&&(r.boundingSphere={center:r.boundingSphere.center.toArray(),radius:r.boundingSphere.radius}),this.boundingBox!==null&&(r.boundingBox={min:r.boundingBox.min.toArray(),max:r.boundingBox.max.toArray()}));function s(a,l){return a[l.uuid]===void 0&&(a[l.uuid]=l.toJSON(e)),l.uuid}if(this.isScene)this.background&&(this.background.isColor?r.background=this.background.toJSON():this.background.isTexture&&(r.background=this.background.toJSON(e).uuid)),this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0&&(r.environment=this.environment.toJSON(e).uuid);else if(this.isMesh||this.isLine||this.isPoints){r.geometry=s(e.geometries,this.geometry);const a=this.geometry.parameters;if(a!==void 0&&a.shapes!==void 0){const l=a.shapes;if(Array.isArray(l))for(let c=0,d=l.length;c<d;c++){const h=l[c];s(e.shapes,h)}else s(e.shapes,l)}}if(this.isSkinnedMesh&&(r.bindMode=this.bindMode,r.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0&&(s(e.skeletons,this.skeleton),r.skeleton=this.skeleton.uuid)),this.material!==void 0)if(Array.isArray(this.material)){const a=[];for(let l=0,c=this.material.length;l<c;l++)a.push(s(e.materials,this.material[l]));r.material=a}else r.material=s(e.materials,this.material);if(this.children.length>0){r.children=[];for(let a=0;a<this.children.length;a++)r.children.push(this.children[a].toJSON(e).object)}if(this.animations.length>0){r.animations=[];for(let a=0;a<this.animations.length;a++){const l=this.animations[a];r.animations.push(s(e.animations,l))}}if(n){const a=o(e.geometries),l=o(e.materials),c=o(e.textures),d=o(e.images),h=o(e.shapes),f=o(e.skeletons),p=o(e.animations),g=o(e.nodes);a.length>0&&(i.geometries=a),l.length>0&&(i.materials=l),c.length>0&&(i.textures=c),d.length>0&&(i.images=d),h.length>0&&(i.shapes=h),f.length>0&&(i.skeletons=f),p.length>0&&(i.animations=p),g.length>0&&(i.nodes=g)}return i.object=r,i;function o(a){const l=[];for(const c in a){const d=a[c];delete d.metadata,l.push(d)}return l}}clone(e){return new this.constructor().copy(this,e)}copy(e,n=!0){if(this.name=e.name,this.up.copy(e.up),this.position.copy(e.position),this.rotation.order=e.rotation.order,this.quaternion.copy(e.quaternion),this.scale.copy(e.scale),this.matrix.copy(e.matrix),this.matrixWorld.copy(e.matrixWorld),this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrixWorldAutoUpdate=e.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=e.matrixWorldNeedsUpdate,this.layers.mask=e.layers.mask,this.visible=e.visible,this.castShadow=e.castShadow,this.receiveShadow=e.receiveShadow,this.frustumCulled=e.frustumCulled,this.renderOrder=e.renderOrder,this.animations=e.animations.slice(),this.userData=JSON.parse(JSON.stringify(e.userData)),n===!0)for(let i=0;i<e.children.length;i++){const r=e.children[i];this.add(r.clone())}return this}}kt.DEFAULT_UP=new O(0,1,0);kt.DEFAULT_MATRIX_AUTO_UPDATE=!0;kt.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;const $n=new O,xi=new O,fu=new O,yi=new O,ss=new O,os=new O,cm=new O,pu=new O,mu=new O,gu=new O,_u=new Rt,vu=new Rt,xu=new Rt;class Jn{constructor(e=new O,n=new O,i=new O){this.a=e,this.b=n,this.c=i}static getNormal(e,n,i,r){r.subVectors(i,n),$n.subVectors(e,n),r.cross($n);const s=r.lengthSq();return s>0?r.multiplyScalar(1/Math.sqrt(s)):r.set(0,0,0)}static getBarycoord(e,n,i,r,s){$n.subVectors(r,n),xi.subVectors(i,n),fu.subVectors(e,n);const o=$n.dot($n),a=$n.dot(xi),l=$n.dot(fu),c=xi.dot(xi),d=xi.dot(fu),h=o*c-a*a;if(h===0)return s.set(0,0,0),null;const f=1/h,p=(c*l-a*d)*f,g=(o*d-a*l)*f;return s.set(1-p-g,g,p)}static containsPoint(e,n,i,r){return this.getBarycoord(e,n,i,r,yi)===null?!1:yi.x>=0&&yi.y>=0&&yi.x+yi.y<=1}static getInterpolation(e,n,i,r,s,o,a,l){return this.getBarycoord(e,n,i,r,yi)===null?(l.x=0,l.y=0,"z"in l&&(l.z=0),"w"in l&&(l.w=0),null):(l.setScalar(0),l.addScaledVector(s,yi.x),l.addScaledVector(o,yi.y),l.addScaledVector(a,yi.z),l)}static getInterpolatedAttribute(e,n,i,r,s,o){return _u.setScalar(0),vu.setScalar(0),xu.setScalar(0),_u.fromBufferAttribute(e,n),vu.fromBufferAttribute(e,i),xu.fromBufferAttribute(e,r),o.setScalar(0),o.addScaledVector(_u,s.x),o.addScaledVector(vu,s.y),o.addScaledVector(xu,s.z),o}static isFrontFacing(e,n,i,r){return $n.subVectors(i,n),xi.subVectors(e,n),$n.cross(xi).dot(r)<0}set(e,n,i){return this.a.copy(e),this.b.copy(n),this.c.copy(i),this}setFromPointsAndIndices(e,n,i,r){return this.a.copy(e[n]),this.b.copy(e[i]),this.c.copy(e[r]),this}setFromAttributeAndIndices(e,n,i,r){return this.a.fromBufferAttribute(e,n),this.b.fromBufferAttribute(e,i),this.c.fromBufferAttribute(e,r),this}clone(){return new this.constructor().copy(this)}copy(e){return this.a.copy(e.a),this.b.copy(e.b),this.c.copy(e.c),this}getArea(){return $n.subVectors(this.c,this.b),xi.subVectors(this.a,this.b),$n.cross(xi).length()*.5}getMidpoint(e){return e.addVectors(this.a,this.b).add(this.c).multiplyScalar(1/3)}getNormal(e){return Jn.getNormal(this.a,this.b,this.c,e)}getPlane(e){return e.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(e,n){return Jn.getBarycoord(e,this.a,this.b,this.c,n)}getInterpolation(e,n,i,r,s){return Jn.getInterpolation(e,this.a,this.b,this.c,n,i,r,s)}containsPoint(e){return Jn.containsPoint(e,this.a,this.b,this.c)}isFrontFacing(e){return Jn.isFrontFacing(this.a,this.b,this.c,e)}intersectsBox(e){return e.intersectsTriangle(this)}closestPointToPoint(e,n){const i=this.a,r=this.b,s=this.c;let o,a;ss.subVectors(r,i),os.subVectors(s,i),pu.subVectors(e,i);const l=ss.dot(pu),c=os.dot(pu);if(l<=0&&c<=0)return n.copy(i);mu.subVectors(e,r);const d=ss.dot(mu),h=os.dot(mu);if(d>=0&&h<=d)return n.copy(r);const f=l*h-d*c;if(f<=0&&l>=0&&d<=0)return o=l/(l-d),n.copy(i).addScaledVector(ss,o);gu.subVectors(e,s);const p=ss.dot(gu),g=os.dot(gu);if(g>=0&&p<=g)return n.copy(s);const x=p*c-l*g;if(x<=0&&c>=0&&g<=0)return a=c/(c-g),n.copy(i).addScaledVector(os,a);const m=d*g-p*h;if(m<=0&&h-d>=0&&p-g>=0)return cm.subVectors(s,r),a=(h-d)/(h-d+(p-g)),n.copy(r).addScaledVector(cm,a);const u=1/(m+x+f);return o=x*u,a=f*u,n.copy(i).addScaledVector(ss,o).addScaledVector(os,a)}equals(e){return e.a.equals(this.a)&&e.b.equals(this.b)&&e.c.equals(this.c)}}const Hv={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},ji={h:0,s:0,l:0},Ba={h:0,s:0,l:0};function yu(t,e,n){return n<0&&(n+=1),n>1&&(n-=1),n<1/6?t+(e-t)*6*n:n<1/2?e:n<2/3?t+(e-t)*6*(2/3-n):t}class ct{constructor(e,n,i){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(e,n,i)}set(e,n,i){if(n===void 0&&i===void 0){const r=e;r&&r.isColor?this.copy(r):typeof r=="number"?this.setHex(r):typeof r=="string"&&this.setStyle(r)}else this.setRGB(e,n,i);return this}setScalar(e){return this.r=e,this.g=e,this.b=e,this}setHex(e,n=In){return e=Math.floor(e),this.r=(e>>16&255)/255,this.g=(e>>8&255)/255,this.b=(e&255)/255,lt.toWorkingColorSpace(this,n),this}setRGB(e,n,i,r=lt.workingColorSpace){return this.r=e,this.g=n,this.b=i,lt.toWorkingColorSpace(this,r),this}setHSL(e,n,i,r=lt.workingColorSpace){if(e=GS(e,1),n=et(n,0,1),i=et(i,0,1),n===0)this.r=this.g=this.b=i;else{const s=i<=.5?i*(1+n):i+n-i*n,o=2*i-s;this.r=yu(o,s,e+1/3),this.g=yu(o,s,e),this.b=yu(o,s,e-1/3)}return lt.toWorkingColorSpace(this,r),this}setStyle(e,n=In){function i(s){s!==void 0&&parseFloat(s)<1&&console.warn("THREE.Color: Alpha component of "+e+" will be ignored.")}let r;if(r=/^(\w+)\(([^\)]*)\)/.exec(e)){let s;const o=r[1],a=r[2];switch(o){case"rgb":case"rgba":if(s=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(a))return i(s[4]),this.setRGB(Math.min(255,parseInt(s[1],10))/255,Math.min(255,parseInt(s[2],10))/255,Math.min(255,parseInt(s[3],10))/255,n);if(s=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(a))return i(s[4]),this.setRGB(Math.min(100,parseInt(s[1],10))/100,Math.min(100,parseInt(s[2],10))/100,Math.min(100,parseInt(s[3],10))/100,n);break;case"hsl":case"hsla":if(s=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(a))return i(s[4]),this.setHSL(parseFloat(s[1])/360,parseFloat(s[2])/100,parseFloat(s[3])/100,n);break;default:console.warn("THREE.Color: Unknown color model "+e)}}else if(r=/^\#([A-Fa-f\d]+)$/.exec(e)){const s=r[1],o=s.length;if(o===3)return this.setRGB(parseInt(s.charAt(0),16)/15,parseInt(s.charAt(1),16)/15,parseInt(s.charAt(2),16)/15,n);if(o===6)return this.setHex(parseInt(s,16),n);console.warn("THREE.Color: Invalid hex color "+e)}else if(e&&e.length>0)return this.setColorName(e,n);return this}setColorName(e,n=In){const i=Hv[e.toLowerCase()];return i!==void 0?this.setHex(i,n):console.warn("THREE.Color: Unknown color "+e),this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(e){return this.r=e.r,this.g=e.g,this.b=e.b,this}copySRGBToLinear(e){return this.r=Pi(e.r),this.g=Pi(e.g),this.b=Pi(e.b),this}copyLinearToSRGB(e){return this.r=Os(e.r),this.g=Os(e.g),this.b=Os(e.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(e=In){return lt.fromWorkingColorSpace(Jt.copy(this),e),Math.round(et(Jt.r*255,0,255))*65536+Math.round(et(Jt.g*255,0,255))*256+Math.round(et(Jt.b*255,0,255))}getHexString(e=In){return("000000"+this.getHex(e).toString(16)).slice(-6)}getHSL(e,n=lt.workingColorSpace){lt.fromWorkingColorSpace(Jt.copy(this),n);const i=Jt.r,r=Jt.g,s=Jt.b,o=Math.max(i,r,s),a=Math.min(i,r,s);let l,c;const d=(a+o)/2;if(a===o)l=0,c=0;else{const h=o-a;switch(c=d<=.5?h/(o+a):h/(2-o-a),o){case i:l=(r-s)/h+(r<s?6:0);break;case r:l=(s-i)/h+2;break;case s:l=(i-r)/h+4;break}l/=6}return e.h=l,e.s=c,e.l=d,e}getRGB(e,n=lt.workingColorSpace){return lt.fromWorkingColorSpace(Jt.copy(this),n),e.r=Jt.r,e.g=Jt.g,e.b=Jt.b,e}getStyle(e=In){lt.fromWorkingColorSpace(Jt.copy(this),e);const n=Jt.r,i=Jt.g,r=Jt.b;return e!==In?`color(${e} ${n.toFixed(3)} ${i.toFixed(3)} ${r.toFixed(3)})`:`rgb(${Math.round(n*255)},${Math.round(i*255)},${Math.round(r*255)})`}offsetHSL(e,n,i){return this.getHSL(ji),this.setHSL(ji.h+e,ji.s+n,ji.l+i)}add(e){return this.r+=e.r,this.g+=e.g,this.b+=e.b,this}addColors(e,n){return this.r=e.r+n.r,this.g=e.g+n.g,this.b=e.b+n.b,this}addScalar(e){return this.r+=e,this.g+=e,this.b+=e,this}sub(e){return this.r=Math.max(0,this.r-e.r),this.g=Math.max(0,this.g-e.g),this.b=Math.max(0,this.b-e.b),this}multiply(e){return this.r*=e.r,this.g*=e.g,this.b*=e.b,this}multiplyScalar(e){return this.r*=e,this.g*=e,this.b*=e,this}lerp(e,n){return this.r+=(e.r-this.r)*n,this.g+=(e.g-this.g)*n,this.b+=(e.b-this.b)*n,this}lerpColors(e,n,i){return this.r=e.r+(n.r-e.r)*i,this.g=e.g+(n.g-e.g)*i,this.b=e.b+(n.b-e.b)*i,this}lerpHSL(e,n){this.getHSL(ji),e.getHSL(Ba);const i=iu(ji.h,Ba.h,n),r=iu(ji.s,Ba.s,n),s=iu(ji.l,Ba.l,n);return this.setHSL(i,r,s),this}setFromVector3(e){return this.r=e.x,this.g=e.y,this.b=e.z,this}applyMatrix3(e){const n=this.r,i=this.g,r=this.b,s=e.elements;return this.r=s[0]*n+s[3]*i+s[6]*r,this.g=s[1]*n+s[4]*i+s[7]*r,this.b=s[2]*n+s[5]*i+s[8]*r,this}equals(e){return e.r===this.r&&e.g===this.g&&e.b===this.b}fromArray(e,n=0){return this.r=e[n],this.g=e[n+1],this.b=e[n+2],this}toArray(e=[],n=0){return e[n]=this.r,e[n+1]=this.g,e[n+2]=this.b,e}fromBufferAttribute(e,n){return this.r=e.getX(n),this.g=e.getY(n),this.b=e.getZ(n),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}}const Jt=new ct;ct.NAMES=Hv;let lM=0;class eo extends $r{constructor(){super(),this.isMaterial=!0,Object.defineProperty(this,"id",{value:lM++}),this.uuid=aa(),this.name="",this.type="Material",this.blending=Is,this.side=hr,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=Od,this.blendDst=Fd,this.blendEquation=br,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new ct(0,0,0),this.blendAlpha=0,this.depthFunc=js,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=qp,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=Zr,this.stencilZFail=Zr,this.stencilZPass=Zr,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(e){this._alphaTest>0!=e>0&&this.version++,this._alphaTest=e}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(e){if(e!==void 0)for(const n in e){const i=e[n];if(i===void 0){console.warn(`THREE.Material: parameter '${n}' has value of undefined.`);continue}const r=this[n];if(r===void 0){console.warn(`THREE.Material: '${n}' is not a property of THREE.${this.type}.`);continue}r&&r.isColor?r.set(i):r&&r.isVector3&&i&&i.isVector3?r.copy(i):this[n]=i}}toJSON(e){const n=e===void 0||typeof e=="string";n&&(e={textures:{},images:{}});const i={metadata:{version:4.6,type:"Material",generator:"Material.toJSON"}};i.uuid=this.uuid,i.type=this.type,this.name!==""&&(i.name=this.name),this.color&&this.color.isColor&&(i.color=this.color.getHex()),this.roughness!==void 0&&(i.roughness=this.roughness),this.metalness!==void 0&&(i.metalness=this.metalness),this.sheen!==void 0&&(i.sheen=this.sheen),this.sheenColor&&this.sheenColor.isColor&&(i.sheenColor=this.sheenColor.getHex()),this.sheenRoughness!==void 0&&(i.sheenRoughness=this.sheenRoughness),this.emissive&&this.emissive.isColor&&(i.emissive=this.emissive.getHex()),this.emissiveIntensity!==void 0&&this.emissiveIntensity!==1&&(i.emissiveIntensity=this.emissiveIntensity),this.specular&&this.specular.isColor&&(i.specular=this.specular.getHex()),this.specularIntensity!==void 0&&(i.specularIntensity=this.specularIntensity),this.specularColor&&this.specularColor.isColor&&(i.specularColor=this.specularColor.getHex()),this.shininess!==void 0&&(i.shininess=this.shininess),this.clearcoat!==void 0&&(i.clearcoat=this.clearcoat),this.clearcoatRoughness!==void 0&&(i.clearcoatRoughness=this.clearcoatRoughness),this.clearcoatMap&&this.clearcoatMap.isTexture&&(i.clearcoatMap=this.clearcoatMap.toJSON(e).uuid),this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture&&(i.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(e).uuid),this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture&&(i.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(e).uuid,i.clearcoatNormalScale=this.clearcoatNormalScale.toArray()),this.dispersion!==void 0&&(i.dispersion=this.dispersion),this.iridescence!==void 0&&(i.iridescence=this.iridescence),this.iridescenceIOR!==void 0&&(i.iridescenceIOR=this.iridescenceIOR),this.iridescenceThicknessRange!==void 0&&(i.iridescenceThicknessRange=this.iridescenceThicknessRange),this.iridescenceMap&&this.iridescenceMap.isTexture&&(i.iridescenceMap=this.iridescenceMap.toJSON(e).uuid),this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture&&(i.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(e).uuid),this.anisotropy!==void 0&&(i.anisotropy=this.anisotropy),this.anisotropyRotation!==void 0&&(i.anisotropyRotation=this.anisotropyRotation),this.anisotropyMap&&this.anisotropyMap.isTexture&&(i.anisotropyMap=this.anisotropyMap.toJSON(e).uuid),this.map&&this.map.isTexture&&(i.map=this.map.toJSON(e).uuid),this.matcap&&this.matcap.isTexture&&(i.matcap=this.matcap.toJSON(e).uuid),this.alphaMap&&this.alphaMap.isTexture&&(i.alphaMap=this.alphaMap.toJSON(e).uuid),this.lightMap&&this.lightMap.isTexture&&(i.lightMap=this.lightMap.toJSON(e).uuid,i.lightMapIntensity=this.lightMapIntensity),this.aoMap&&this.aoMap.isTexture&&(i.aoMap=this.aoMap.toJSON(e).uuid,i.aoMapIntensity=this.aoMapIntensity),this.bumpMap&&this.bumpMap.isTexture&&(i.bumpMap=this.bumpMap.toJSON(e).uuid,i.bumpScale=this.bumpScale),this.normalMap&&this.normalMap.isTexture&&(i.normalMap=this.normalMap.toJSON(e).uuid,i.normalMapType=this.normalMapType,i.normalScale=this.normalScale.toArray()),this.displacementMap&&this.displacementMap.isTexture&&(i.displacementMap=this.displacementMap.toJSON(e).uuid,i.displacementScale=this.displacementScale,i.displacementBias=this.displacementBias),this.roughnessMap&&this.roughnessMap.isTexture&&(i.roughnessMap=this.roughnessMap.toJSON(e).uuid),this.metalnessMap&&this.metalnessMap.isTexture&&(i.metalnessMap=this.metalnessMap.toJSON(e).uuid),this.emissiveMap&&this.emissiveMap.isTexture&&(i.emissiveMap=this.emissiveMap.toJSON(e).uuid),this.specularMap&&this.specularMap.isTexture&&(i.specularMap=this.specularMap.toJSON(e).uuid),this.specularIntensityMap&&this.specularIntensityMap.isTexture&&(i.specularIntensityMap=this.specularIntensityMap.toJSON(e).uuid),this.specularColorMap&&this.specularColorMap.isTexture&&(i.specularColorMap=this.specularColorMap.toJSON(e).uuid),this.envMap&&this.envMap.isTexture&&(i.envMap=this.envMap.toJSON(e).uuid,this.combine!==void 0&&(i.combine=this.combine)),this.envMapRotation!==void 0&&(i.envMapRotation=this.envMapRotation.toArray()),this.envMapIntensity!==void 0&&(i.envMapIntensity=this.envMapIntensity),this.reflectivity!==void 0&&(i.reflectivity=this.reflectivity),this.refractionRatio!==void 0&&(i.refractionRatio=this.refractionRatio),this.gradientMap&&this.gradientMap.isTexture&&(i.gradientMap=this.gradientMap.toJSON(e).uuid),this.transmission!==void 0&&(i.transmission=this.transmission),this.transmissionMap&&this.transmissionMap.isTexture&&(i.transmissionMap=this.transmissionMap.toJSON(e).uuid),this.thickness!==void 0&&(i.thickness=this.thickness),this.thicknessMap&&this.thicknessMap.isTexture&&(i.thicknessMap=this.thicknessMap.toJSON(e).uuid),this.attenuationDistance!==void 0&&this.attenuationDistance!==1/0&&(i.attenuationDistance=this.attenuationDistance),this.attenuationColor!==void 0&&(i.attenuationColor=this.attenuationColor.getHex()),this.size!==void 0&&(i.size=this.size),this.shadowSide!==null&&(i.shadowSide=this.shadowSide),this.sizeAttenuation!==void 0&&(i.sizeAttenuation=this.sizeAttenuation),this.blending!==Is&&(i.blending=this.blending),this.side!==hr&&(i.side=this.side),this.vertexColors===!0&&(i.vertexColors=!0),this.opacity<1&&(i.opacity=this.opacity),this.transparent===!0&&(i.transparent=!0),this.blendSrc!==Od&&(i.blendSrc=this.blendSrc),this.blendDst!==Fd&&(i.blendDst=this.blendDst),this.blendEquation!==br&&(i.blendEquation=this.blendEquation),this.blendSrcAlpha!==null&&(i.blendSrcAlpha=this.blendSrcAlpha),this.blendDstAlpha!==null&&(i.blendDstAlpha=this.blendDstAlpha),this.blendEquationAlpha!==null&&(i.blendEquationAlpha=this.blendEquationAlpha),this.blendColor&&this.blendColor.isColor&&(i.blendColor=this.blendColor.getHex()),this.blendAlpha!==0&&(i.blendAlpha=this.blendAlpha),this.depthFunc!==js&&(i.depthFunc=this.depthFunc),this.depthTest===!1&&(i.depthTest=this.depthTest),this.depthWrite===!1&&(i.depthWrite=this.depthWrite),this.colorWrite===!1&&(i.colorWrite=this.colorWrite),this.stencilWriteMask!==255&&(i.stencilWriteMask=this.stencilWriteMask),this.stencilFunc!==qp&&(i.stencilFunc=this.stencilFunc),this.stencilRef!==0&&(i.stencilRef=this.stencilRef),this.stencilFuncMask!==255&&(i.stencilFuncMask=this.stencilFuncMask),this.stencilFail!==Zr&&(i.stencilFail=this.stencilFail),this.stencilZFail!==Zr&&(i.stencilZFail=this.stencilZFail),this.stencilZPass!==Zr&&(i.stencilZPass=this.stencilZPass),this.stencilWrite===!0&&(i.stencilWrite=this.stencilWrite),this.rotation!==void 0&&this.rotation!==0&&(i.rotation=this.rotation),this.polygonOffset===!0&&(i.polygonOffset=!0),this.polygonOffsetFactor!==0&&(i.polygonOffsetFactor=this.polygonOffsetFactor),this.polygonOffsetUnits!==0&&(i.polygonOffsetUnits=this.polygonOffsetUnits),this.linewidth!==void 0&&this.linewidth!==1&&(i.linewidth=this.linewidth),this.dashSize!==void 0&&(i.dashSize=this.dashSize),this.gapSize!==void 0&&(i.gapSize=this.gapSize),this.scale!==void 0&&(i.scale=this.scale),this.dithering===!0&&(i.dithering=!0),this.alphaTest>0&&(i.alphaTest=this.alphaTest),this.alphaHash===!0&&(i.alphaHash=!0),this.alphaToCoverage===!0&&(i.alphaToCoverage=!0),this.premultipliedAlpha===!0&&(i.premultipliedAlpha=!0),this.forceSinglePass===!0&&(i.forceSinglePass=!0),this.wireframe===!0&&(i.wireframe=!0),this.wireframeLinewidth>1&&(i.wireframeLinewidth=this.wireframeLinewidth),this.wireframeLinecap!=="round"&&(i.wireframeLinecap=this.wireframeLinecap),this.wireframeLinejoin!=="round"&&(i.wireframeLinejoin=this.wireframeLinejoin),this.flatShading===!0&&(i.flatShading=!0),this.visible===!1&&(i.visible=!1),this.toneMapped===!1&&(i.toneMapped=!1),this.fog===!1&&(i.fog=!1),Object.keys(this.userData).length>0&&(i.userData=this.userData);function r(s){const o=[];for(const a in s){const l=s[a];delete l.metadata,o.push(l)}return o}if(n){const s=r(e.textures),o=r(e.images);s.length>0&&(i.textures=s),o.length>0&&(i.images=o)}return i}clone(){return new this.constructor().copy(this)}copy(e){this.name=e.name,this.blending=e.blending,this.side=e.side,this.vertexColors=e.vertexColors,this.opacity=e.opacity,this.transparent=e.transparent,this.blendSrc=e.blendSrc,this.blendDst=e.blendDst,this.blendEquation=e.blendEquation,this.blendSrcAlpha=e.blendSrcAlpha,this.blendDstAlpha=e.blendDstAlpha,this.blendEquationAlpha=e.blendEquationAlpha,this.blendColor.copy(e.blendColor),this.blendAlpha=e.blendAlpha,this.depthFunc=e.depthFunc,this.depthTest=e.depthTest,this.depthWrite=e.depthWrite,this.stencilWriteMask=e.stencilWriteMask,this.stencilFunc=e.stencilFunc,this.stencilRef=e.stencilRef,this.stencilFuncMask=e.stencilFuncMask,this.stencilFail=e.stencilFail,this.stencilZFail=e.stencilZFail,this.stencilZPass=e.stencilZPass,this.stencilWrite=e.stencilWrite;const n=e.clippingPlanes;let i=null;if(n!==null){const r=n.length;i=new Array(r);for(let s=0;s!==r;++s)i[s]=n[s].clone()}return this.clippingPlanes=i,this.clipIntersection=e.clipIntersection,this.clipShadows=e.clipShadows,this.shadowSide=e.shadowSide,this.colorWrite=e.colorWrite,this.precision=e.precision,this.polygonOffset=e.polygonOffset,this.polygonOffsetFactor=e.polygonOffsetFactor,this.polygonOffsetUnits=e.polygonOffsetUnits,this.dithering=e.dithering,this.alphaTest=e.alphaTest,this.alphaHash=e.alphaHash,this.alphaToCoverage=e.alphaToCoverage,this.premultipliedAlpha=e.premultipliedAlpha,this.forceSinglePass=e.forceSinglePass,this.visible=e.visible,this.toneMapped=e.toneMapped,this.userData=JSON.parse(JSON.stringify(e.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(e){e===!0&&this.version++}onBuild(){console.warn("Material: onBuild() has been removed.")}}class Vv extends eo{constructor(e){super(),this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new ct(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new hi,this.combine=wv,this.reflectivity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.fog=e.fog,this}}const Dt=new O,za=new Fe;class di{constructor(e,n,i=!1){if(Array.isArray(e))throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,this.name="",this.array=e,this.itemSize=n,this.count=e!==void 0?e.length/n:0,this.normalized=i,this.usage=Kp,this.updateRanges=[],this.gpuType=Ci,this.version=0}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,n){this.updateRanges.push({start:e,count:n})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.name=e.name,this.array=new e.array.constructor(e.array),this.itemSize=e.itemSize,this.count=e.count,this.normalized=e.normalized,this.usage=e.usage,this.gpuType=e.gpuType,this}copyAt(e,n,i){e*=this.itemSize,i*=n.itemSize;for(let r=0,s=this.itemSize;r<s;r++)this.array[e+r]=n.array[i+r];return this}copyArray(e){return this.array.set(e),this}applyMatrix3(e){if(this.itemSize===2)for(let n=0,i=this.count;n<i;n++)za.fromBufferAttribute(this,n),za.applyMatrix3(e),this.setXY(n,za.x,za.y);else if(this.itemSize===3)for(let n=0,i=this.count;n<i;n++)Dt.fromBufferAttribute(this,n),Dt.applyMatrix3(e),this.setXYZ(n,Dt.x,Dt.y,Dt.z);return this}applyMatrix4(e){for(let n=0,i=this.count;n<i;n++)Dt.fromBufferAttribute(this,n),Dt.applyMatrix4(e),this.setXYZ(n,Dt.x,Dt.y,Dt.z);return this}applyNormalMatrix(e){for(let n=0,i=this.count;n<i;n++)Dt.fromBufferAttribute(this,n),Dt.applyNormalMatrix(e),this.setXYZ(n,Dt.x,Dt.y,Dt.z);return this}transformDirection(e){for(let n=0,i=this.count;n<i;n++)Dt.fromBufferAttribute(this,n),Dt.transformDirection(e),this.setXYZ(n,Dt.x,Dt.y,Dt.z);return this}set(e,n=0){return this.array.set(e,n),this}getComponent(e,n){let i=this.array[e*this.itemSize+n];return this.normalized&&(i=ho(i,this.array)),i}setComponent(e,n,i){return this.normalized&&(i=cn(i,this.array)),this.array[e*this.itemSize+n]=i,this}getX(e){let n=this.array[e*this.itemSize];return this.normalized&&(n=ho(n,this.array)),n}setX(e,n){return this.normalized&&(n=cn(n,this.array)),this.array[e*this.itemSize]=n,this}getY(e){let n=this.array[e*this.itemSize+1];return this.normalized&&(n=ho(n,this.array)),n}setY(e,n){return this.normalized&&(n=cn(n,this.array)),this.array[e*this.itemSize+1]=n,this}getZ(e){let n=this.array[e*this.itemSize+2];return this.normalized&&(n=ho(n,this.array)),n}setZ(e,n){return this.normalized&&(n=cn(n,this.array)),this.array[e*this.itemSize+2]=n,this}getW(e){let n=this.array[e*this.itemSize+3];return this.normalized&&(n=ho(n,this.array)),n}setW(e,n){return this.normalized&&(n=cn(n,this.array)),this.array[e*this.itemSize+3]=n,this}setXY(e,n,i){return e*=this.itemSize,this.normalized&&(n=cn(n,this.array),i=cn(i,this.array)),this.array[e+0]=n,this.array[e+1]=i,this}setXYZ(e,n,i,r){return e*=this.itemSize,this.normalized&&(n=cn(n,this.array),i=cn(i,this.array),r=cn(r,this.array)),this.array[e+0]=n,this.array[e+1]=i,this.array[e+2]=r,this}setXYZW(e,n,i,r,s){return e*=this.itemSize,this.normalized&&(n=cn(n,this.array),i=cn(i,this.array),r=cn(r,this.array),s=cn(s,this.array)),this.array[e+0]=n,this.array[e+1]=i,this.array[e+2]=r,this.array[e+3]=s,this}onUpload(e){return this.onUploadCallback=e,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){const e={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};return this.name!==""&&(e.name=this.name),this.usage!==Kp&&(e.usage=this.usage),e}}class Gv extends di{constructor(e,n,i){super(new Uint16Array(e),n,i)}}class jv extends di{constructor(e,n,i){super(new Uint32Array(e),n,i)}}class vn extends di{constructor(e,n,i){super(new Float32Array(e),n,i)}}let cM=0;const Dn=new mt,Su=new kt,as=new O,Mn=new la,go=new la,Ht=new O;class Cn extends $r{constructor(){super(),this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:cM++}),this.uuid=aa(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={}}getIndex(){return this.index}setIndex(e){return Array.isArray(e)?this.index=new(kv(e)?jv:Gv)(e,1):this.index=e,this}setIndirect(e){return this.indirect=e,this}getIndirect(){return this.indirect}getAttribute(e){return this.attributes[e]}setAttribute(e,n){return this.attributes[e]=n,this}deleteAttribute(e){return delete this.attributes[e],this}hasAttribute(e){return this.attributes[e]!==void 0}addGroup(e,n,i=0){this.groups.push({start:e,count:n,materialIndex:i})}clearGroups(){this.groups=[]}setDrawRange(e,n){this.drawRange.start=e,this.drawRange.count=n}applyMatrix4(e){const n=this.attributes.position;n!==void 0&&(n.applyMatrix4(e),n.needsUpdate=!0);const i=this.attributes.normal;if(i!==void 0){const s=new Ze().getNormalMatrix(e);i.applyNormalMatrix(s),i.needsUpdate=!0}const r=this.attributes.tangent;return r!==void 0&&(r.transformDirection(e),r.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this}applyQuaternion(e){return Dn.makeRotationFromQuaternion(e),this.applyMatrix4(Dn),this}rotateX(e){return Dn.makeRotationX(e),this.applyMatrix4(Dn),this}rotateY(e){return Dn.makeRotationY(e),this.applyMatrix4(Dn),this}rotateZ(e){return Dn.makeRotationZ(e),this.applyMatrix4(Dn),this}translate(e,n,i){return Dn.makeTranslation(e,n,i),this.applyMatrix4(Dn),this}scale(e,n,i){return Dn.makeScale(e,n,i),this.applyMatrix4(Dn),this}lookAt(e){return Su.lookAt(e),Su.updateMatrix(),this.applyMatrix4(Su.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(as).negate(),this.translate(as.x,as.y,as.z),this}setFromPoints(e){const n=this.getAttribute("position");if(n===void 0){const i=[];for(let r=0,s=e.length;r<s;r++){const o=e[r];i.push(o.x,o.y,o.z||0)}this.setAttribute("position",new vn(i,3))}else{const i=Math.min(e.length,n.count);for(let r=0;r<i;r++){const s=e[r];n.setXYZ(r,s.x,s.y,s.z||0)}e.length>n.count&&console.warn("THREE.BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry."),n.needsUpdate=!0}return this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new la);const e=this.attributes.position,n=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){console.error("THREE.BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new O(-1/0,-1/0,-1/0),new O(1/0,1/0,1/0));return}if(e!==void 0){if(this.boundingBox.setFromBufferAttribute(e),n)for(let i=0,r=n.length;i<r;i++){const s=n[i];Mn.setFromBufferAttribute(s),this.morphTargetsRelative?(Ht.addVectors(this.boundingBox.min,Mn.min),this.boundingBox.expandByPoint(Ht),Ht.addVectors(this.boundingBox.max,Mn.max),this.boundingBox.expandByPoint(Ht)):(this.boundingBox.expandByPoint(Mn.min),this.boundingBox.expandByPoint(Mn.max))}}else this.boundingBox.makeEmpty();(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))&&console.error('THREE.BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new Sc);const e=this.attributes.position,n=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){console.error("THREE.BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new O,1/0);return}if(e){const i=this.boundingSphere.center;if(Mn.setFromBufferAttribute(e),n)for(let s=0,o=n.length;s<o;s++){const a=n[s];go.setFromBufferAttribute(a),this.morphTargetsRelative?(Ht.addVectors(Mn.min,go.min),Mn.expandByPoint(Ht),Ht.addVectors(Mn.max,go.max),Mn.expandByPoint(Ht)):(Mn.expandByPoint(go.min),Mn.expandByPoint(go.max))}Mn.getCenter(i);let r=0;for(let s=0,o=e.count;s<o;s++)Ht.fromBufferAttribute(e,s),r=Math.max(r,i.distanceToSquared(Ht));if(n)for(let s=0,o=n.length;s<o;s++){const a=n[s],l=this.morphTargetsRelative;for(let c=0,d=a.count;c<d;c++)Ht.fromBufferAttribute(a,c),l&&(as.fromBufferAttribute(e,c),Ht.add(as)),r=Math.max(r,i.distanceToSquared(Ht))}this.boundingSphere.radius=Math.sqrt(r),isNaN(this.boundingSphere.radius)&&console.error('THREE.BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){const e=this.index,n=this.attributes;if(e===null||n.position===void 0||n.normal===void 0||n.uv===void 0){console.error("THREE.BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}const i=n.position,r=n.normal,s=n.uv;this.hasAttribute("tangent")===!1&&this.setAttribute("tangent",new di(new Float32Array(4*i.count),4));const o=this.getAttribute("tangent"),a=[],l=[];for(let P=0;P<i.count;P++)a[P]=new O,l[P]=new O;const c=new O,d=new O,h=new O,f=new Fe,p=new Fe,g=new Fe,x=new O,m=new O;function u(P,E,S){c.fromBufferAttribute(i,P),d.fromBufferAttribute(i,E),h.fromBufferAttribute(i,S),f.fromBufferAttribute(s,P),p.fromBufferAttribute(s,E),g.fromBufferAttribute(s,S),d.sub(c),h.sub(c),p.sub(f),g.sub(f);const D=1/(p.x*g.y-g.x*p.y);isFinite(D)&&(x.copy(d).multiplyScalar(g.y).addScaledVector(h,-p.y).multiplyScalar(D),m.copy(h).multiplyScalar(p.x).addScaledVector(d,-g.x).multiplyScalar(D),a[P].add(x),a[E].add(x),a[S].add(x),l[P].add(m),l[E].add(m),l[S].add(m))}let _=this.groups;_.length===0&&(_=[{start:0,count:e.count}]);for(let P=0,E=_.length;P<E;++P){const S=_[P],D=S.start,X=S.count;for(let H=D,U=D+X;H<U;H+=3)u(e.getX(H+0),e.getX(H+1),e.getX(H+2))}const v=new O,M=new O,R=new O,C=new O;function A(P){R.fromBufferAttribute(r,P),C.copy(R);const E=a[P];v.copy(E),v.sub(R.multiplyScalar(R.dot(E))).normalize(),M.crossVectors(C,E);const D=M.dot(l[P])<0?-1:1;o.setXYZW(P,v.x,v.y,v.z,D)}for(let P=0,E=_.length;P<E;++P){const S=_[P],D=S.start,X=S.count;for(let H=D,U=D+X;H<U;H+=3)A(e.getX(H+0)),A(e.getX(H+1)),A(e.getX(H+2))}}computeVertexNormals(){const e=this.index,n=this.getAttribute("position");if(n!==void 0){let i=this.getAttribute("normal");if(i===void 0)i=new di(new Float32Array(n.count*3),3),this.setAttribute("normal",i);else for(let f=0,p=i.count;f<p;f++)i.setXYZ(f,0,0,0);const r=new O,s=new O,o=new O,a=new O,l=new O,c=new O,d=new O,h=new O;if(e)for(let f=0,p=e.count;f<p;f+=3){const g=e.getX(f+0),x=e.getX(f+1),m=e.getX(f+2);r.fromBufferAttribute(n,g),s.fromBufferAttribute(n,x),o.fromBufferAttribute(n,m),d.subVectors(o,s),h.subVectors(r,s),d.cross(h),a.fromBufferAttribute(i,g),l.fromBufferAttribute(i,x),c.fromBufferAttribute(i,m),a.add(d),l.add(d),c.add(d),i.setXYZ(g,a.x,a.y,a.z),i.setXYZ(x,l.x,l.y,l.z),i.setXYZ(m,c.x,c.y,c.z)}else for(let f=0,p=n.count;f<p;f+=3)r.fromBufferAttribute(n,f+0),s.fromBufferAttribute(n,f+1),o.fromBufferAttribute(n,f+2),d.subVectors(o,s),h.subVectors(r,s),d.cross(h),i.setXYZ(f+0,d.x,d.y,d.z),i.setXYZ(f+1,d.x,d.y,d.z),i.setXYZ(f+2,d.x,d.y,d.z);this.normalizeNormals(),i.needsUpdate=!0}}normalizeNormals(){const e=this.attributes.normal;for(let n=0,i=e.count;n<i;n++)Ht.fromBufferAttribute(e,n),Ht.normalize(),e.setXYZ(n,Ht.x,Ht.y,Ht.z)}toNonIndexed(){function e(a,l){const c=a.array,d=a.itemSize,h=a.normalized,f=new c.constructor(l.length*d);let p=0,g=0;for(let x=0,m=l.length;x<m;x++){a.isInterleavedBufferAttribute?p=l[x]*a.data.stride+a.offset:p=l[x]*d;for(let u=0;u<d;u++)f[g++]=c[p++]}return new di(f,d,h)}if(this.index===null)return console.warn("THREE.BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;const n=new Cn,i=this.index.array,r=this.attributes;for(const a in r){const l=r[a],c=e(l,i);n.setAttribute(a,c)}const s=this.morphAttributes;for(const a in s){const l=[],c=s[a];for(let d=0,h=c.length;d<h;d++){const f=c[d],p=e(f,i);l.push(p)}n.morphAttributes[a]=l}n.morphTargetsRelative=this.morphTargetsRelative;const o=this.groups;for(let a=0,l=o.length;a<l;a++){const c=o[a];n.addGroup(c.start,c.count,c.materialIndex)}return n}toJSON(){const e={metadata:{version:4.6,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(e.uuid=this.uuid,e.type=this.type,this.name!==""&&(e.name=this.name),Object.keys(this.userData).length>0&&(e.userData=this.userData),this.parameters!==void 0){const l=this.parameters;for(const c in l)l[c]!==void 0&&(e[c]=l[c]);return e}e.data={attributes:{}};const n=this.index;n!==null&&(e.data.index={type:n.array.constructor.name,array:Array.prototype.slice.call(n.array)});const i=this.attributes;for(const l in i){const c=i[l];e.data.attributes[l]=c.toJSON(e.data)}const r={};let s=!1;for(const l in this.morphAttributes){const c=this.morphAttributes[l],d=[];for(let h=0,f=c.length;h<f;h++){const p=c[h];d.push(p.toJSON(e.data))}d.length>0&&(r[l]=d,s=!0)}s&&(e.data.morphAttributes=r,e.data.morphTargetsRelative=this.morphTargetsRelative);const o=this.groups;o.length>0&&(e.data.groups=JSON.parse(JSON.stringify(o)));const a=this.boundingSphere;return a!==null&&(e.data.boundingSphere={center:a.center.toArray(),radius:a.radius}),e}clone(){return new this.constructor().copy(this)}copy(e){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;const n={};this.name=e.name;const i=e.index;i!==null&&this.setIndex(i.clone(n));const r=e.attributes;for(const c in r){const d=r[c];this.setAttribute(c,d.clone(n))}const s=e.morphAttributes;for(const c in s){const d=[],h=s[c];for(let f=0,p=h.length;f<p;f++)d.push(h[f].clone(n));this.morphAttributes[c]=d}this.morphTargetsRelative=e.morphTargetsRelative;const o=e.groups;for(let c=0,d=o.length;c<d;c++){const h=o[c];this.addGroup(h.start,h.count,h.materialIndex)}const a=e.boundingBox;a!==null&&(this.boundingBox=a.clone());const l=e.boundingSphere;return l!==null&&(this.boundingSphere=l.clone()),this.drawRange.start=e.drawRange.start,this.drawRange.count=e.drawRange.count,this.userData=e.userData,this}dispose(){this.dispatchEvent({type:"dispose"})}}const um=new mt,Sr=new Mc,Ha=new Sc,dm=new O,Va=new O,Ga=new O,ja=new O,Mu=new O,Wa=new O,hm=new O,Xa=new O;class Tn extends kt{constructor(e=new Cn,n=new Vv){super(),this.isMesh=!0,this.type="Mesh",this.geometry=e,this.material=n,this.updateMorphTargets()}copy(e,n){return super.copy(e,n),e.morphTargetInfluences!==void 0&&(this.morphTargetInfluences=e.morphTargetInfluences.slice()),e.morphTargetDictionary!==void 0&&(this.morphTargetDictionary=Object.assign({},e.morphTargetDictionary)),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}updateMorphTargets(){const n=this.geometry.morphAttributes,i=Object.keys(n);if(i.length>0){const r=n[i[0]];if(r!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,o=r.length;s<o;s++){const a=r[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[a]=s}}}}getVertexPosition(e,n){const i=this.geometry,r=i.attributes.position,s=i.morphAttributes.position,o=i.morphTargetsRelative;n.fromBufferAttribute(r,e);const a=this.morphTargetInfluences;if(s&&a){Wa.set(0,0,0);for(let l=0,c=s.length;l<c;l++){const d=a[l],h=s[l];d!==0&&(Mu.fromBufferAttribute(h,e),o?Wa.addScaledVector(Mu,d):Wa.addScaledVector(Mu.sub(n),d))}n.add(Wa)}return n}raycast(e,n){const i=this.geometry,r=this.material,s=this.matrixWorld;r!==void 0&&(i.boundingSphere===null&&i.computeBoundingSphere(),Ha.copy(i.boundingSphere),Ha.applyMatrix4(s),Sr.copy(e.ray).recast(e.near),!(Ha.containsPoint(Sr.origin)===!1&&(Sr.intersectSphere(Ha,dm)===null||Sr.origin.distanceToSquared(dm)>(e.far-e.near)**2))&&(um.copy(s).invert(),Sr.copy(e.ray).applyMatrix4(um),!(i.boundingBox!==null&&Sr.intersectsBox(i.boundingBox)===!1)&&this._computeIntersections(e,n,Sr)))}_computeIntersections(e,n,i){let r;const s=this.geometry,o=this.material,a=s.index,l=s.attributes.position,c=s.attributes.uv,d=s.attributes.uv1,h=s.attributes.normal,f=s.groups,p=s.drawRange;if(a!==null)if(Array.isArray(o))for(let g=0,x=f.length;g<x;g++){const m=f[g],u=o[m.materialIndex],_=Math.max(m.start,p.start),v=Math.min(a.count,Math.min(m.start+m.count,p.start+p.count));for(let M=_,R=v;M<R;M+=3){const C=a.getX(M),A=a.getX(M+1),P=a.getX(M+2);r=$a(this,u,e,i,c,d,h,C,A,P),r&&(r.faceIndex=Math.floor(M/3),r.face.materialIndex=m.materialIndex,n.push(r))}}else{const g=Math.max(0,p.start),x=Math.min(a.count,p.start+p.count);for(let m=g,u=x;m<u;m+=3){const _=a.getX(m),v=a.getX(m+1),M=a.getX(m+2);r=$a(this,o,e,i,c,d,h,_,v,M),r&&(r.faceIndex=Math.floor(m/3),n.push(r))}}else if(l!==void 0)if(Array.isArray(o))for(let g=0,x=f.length;g<x;g++){const m=f[g],u=o[m.materialIndex],_=Math.max(m.start,p.start),v=Math.min(l.count,Math.min(m.start+m.count,p.start+p.count));for(let M=_,R=v;M<R;M+=3){const C=M,A=M+1,P=M+2;r=$a(this,u,e,i,c,d,h,C,A,P),r&&(r.faceIndex=Math.floor(M/3),r.face.materialIndex=m.materialIndex,n.push(r))}}else{const g=Math.max(0,p.start),x=Math.min(l.count,p.start+p.count);for(let m=g,u=x;m<u;m+=3){const _=m,v=m+1,M=m+2;r=$a(this,o,e,i,c,d,h,_,v,M),r&&(r.faceIndex=Math.floor(m/3),n.push(r))}}}}function uM(t,e,n,i,r,s,o,a){let l;if(e.side===gn?l=i.intersectTriangle(o,s,r,!0,a):l=i.intersectTriangle(r,s,o,e.side===hr,a),l===null)return null;Xa.copy(a),Xa.applyMatrix4(t.matrixWorld);const c=n.ray.origin.distanceTo(Xa);return c<n.near||c>n.far?null:{distance:c,point:Xa.clone(),object:t}}function $a(t,e,n,i,r,s,o,a,l,c){t.getVertexPosition(a,Va),t.getVertexPosition(l,Ga),t.getVertexPosition(c,ja);const d=uM(t,e,n,i,Va,Ga,ja,hm);if(d){const h=new O;Jn.getBarycoord(hm,Va,Ga,ja,h),r&&(d.uv=Jn.getInterpolatedAttribute(r,a,l,c,h,new Fe)),s&&(d.uv1=Jn.getInterpolatedAttribute(s,a,l,c,h,new Fe)),o&&(d.normal=Jn.getInterpolatedAttribute(o,a,l,c,h,new O),d.normal.dot(i.direction)>0&&d.normal.multiplyScalar(-1));const f={a,b:l,c,normal:new O,materialIndex:0};Jn.getNormal(Va,Ga,ja,f.normal),d.face=f,d.barycoord=h}return d}class ca extends Cn{constructor(e=1,n=1,i=1,r=1,s=1,o=1){super(),this.type="BoxGeometry",this.parameters={width:e,height:n,depth:i,widthSegments:r,heightSegments:s,depthSegments:o};const a=this;r=Math.floor(r),s=Math.floor(s),o=Math.floor(o);const l=[],c=[],d=[],h=[];let f=0,p=0;g("z","y","x",-1,-1,i,n,e,o,s,0),g("z","y","x",1,-1,i,n,-e,o,s,1),g("x","z","y",1,1,e,i,n,r,o,2),g("x","z","y",1,-1,e,i,-n,r,o,3),g("x","y","z",1,-1,e,n,i,r,s,4),g("x","y","z",-1,-1,e,n,-i,r,s,5),this.setIndex(l),this.setAttribute("position",new vn(c,3)),this.setAttribute("normal",new vn(d,3)),this.setAttribute("uv",new vn(h,2));function g(x,m,u,_,v,M,R,C,A,P,E){const S=M/A,D=R/P,X=M/2,H=R/2,U=C/2,Y=A+1,V=P+1;let J=0,N=0;const j=new O;for(let Z=0;Z<V;Z++){const fe=Z*D-H;for(let _e=0;_e<Y;_e++){const Re=_e*S-X;j[x]=Re*_,j[m]=fe*v,j[u]=U,c.push(j.x,j.y,j.z),j[x]=0,j[m]=0,j[u]=C>0?1:-1,d.push(j.x,j.y,j.z),h.push(_e/A),h.push(1-Z/P),J+=1}}for(let Z=0;Z<P;Z++)for(let fe=0;fe<A;fe++){const _e=f+fe+Y*Z,Re=f+fe+Y*(Z+1),I=f+(fe+1)+Y*(Z+1),z=f+(fe+1)+Y*Z;l.push(_e,Re,z),l.push(Re,I,z),N+=6}a.addGroup(p,N,E),p+=N,f+=J}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new ca(e.width,e.height,e.depth,e.widthSegments,e.heightSegments,e.depthSegments)}}function Ks(t){const e={};for(const n in t){e[n]={};for(const i in t[n]){const r=t[n][i];r&&(r.isColor||r.isMatrix3||r.isMatrix4||r.isVector2||r.isVector3||r.isVector4||r.isTexture||r.isQuaternion)?r.isRenderTargetTexture?(console.warn("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),e[n][i]=null):e[n][i]=r.clone():Array.isArray(r)?e[n][i]=r.slice():e[n][i]=r}}return e}function nn(t){const e={};for(let n=0;n<t.length;n++){const i=Ks(t[n]);for(const r in i)e[r]=i[r]}return e}function dM(t){const e=[];for(let n=0;n<t.length;n++)e.push(t[n].clone());return e}function Wv(t){const e=t.getRenderTarget();return e===null?t.outputColorSpace:e.isXRRenderTarget===!0?e.texture.colorSpace:lt.workingColorSpace}const hM={clone:Ks,merge:nn};var fM=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,pM=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`;class fr extends eo{constructor(e){super(),this.isShaderMaterial=!0,this.type="ShaderMaterial",this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=fM,this.fragmentShader=pM,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,e!==void 0&&this.setValues(e)}copy(e){return super.copy(e),this.fragmentShader=e.fragmentShader,this.vertexShader=e.vertexShader,this.uniforms=Ks(e.uniforms),this.uniformsGroups=dM(e.uniformsGroups),this.defines=Object.assign({},e.defines),this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.fog=e.fog,this.lights=e.lights,this.clipping=e.clipping,this.extensions=Object.assign({},e.extensions),this.glslVersion=e.glslVersion,this}toJSON(e){const n=super.toJSON(e);n.glslVersion=this.glslVersion,n.uniforms={};for(const r in this.uniforms){const o=this.uniforms[r].value;o&&o.isTexture?n.uniforms[r]={type:"t",value:o.toJSON(e).uuid}:o&&o.isColor?n.uniforms[r]={type:"c",value:o.getHex()}:o&&o.isVector2?n.uniforms[r]={type:"v2",value:o.toArray()}:o&&o.isVector3?n.uniforms[r]={type:"v3",value:o.toArray()}:o&&o.isVector4?n.uniforms[r]={type:"v4",value:o.toArray()}:o&&o.isMatrix3?n.uniforms[r]={type:"m3",value:o.toArray()}:o&&o.isMatrix4?n.uniforms[r]={type:"m4",value:o.toArray()}:n.uniforms[r]={value:o}}Object.keys(this.defines).length>0&&(n.defines=this.defines),n.vertexShader=this.vertexShader,n.fragmentShader=this.fragmentShader,n.lights=this.lights,n.clipping=this.clipping;const i={};for(const r in this.extensions)this.extensions[r]===!0&&(i[r]=!0);return Object.keys(i).length>0&&(n.extensions=i),n}}class Xv extends kt{constructor(){super(),this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new mt,this.projectionMatrix=new mt,this.projectionMatrixInverse=new mt,this.coordinateSystem=bi}copy(e,n){return super.copy(e,n),this.matrixWorldInverse.copy(e.matrixWorldInverse),this.projectionMatrix.copy(e.projectionMatrix),this.projectionMatrixInverse.copy(e.projectionMatrixInverse),this.coordinateSystem=e.coordinateSystem,this}getWorldDirection(e){return super.getWorldDirection(e).negate()}updateMatrixWorld(e){super.updateMatrixWorld(e),this.matrixWorldInverse.copy(this.matrixWorld).invert()}updateWorldMatrix(e,n){super.updateWorldMatrix(e,n),this.matrixWorldInverse.copy(this.matrixWorld).invert()}clone(){return new this.constructor().copy(this)}}const Wi=new O,fm=new Fe,pm=new Fe;class Fn extends Xv{constructor(e=50,n=1,i=.1,r=2e3){super(),this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=e,this.zoom=1,this.near=i,this.far=r,this.focus=10,this.aspect=n,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(e,n){return super.copy(e,n),this.fov=e.fov,this.zoom=e.zoom,this.near=e.near,this.far=e.far,this.focus=e.focus,this.aspect=e.aspect,this.view=e.view===null?null:Object.assign({},e.view),this.filmGauge=e.filmGauge,this.filmOffset=e.filmOffset,this}setFocalLength(e){const n=.5*this.getFilmHeight()/e;this.fov=Sh*2*Math.atan(n),this.updateProjectionMatrix()}getFocalLength(){const e=Math.tan(Ml*.5*this.fov);return .5*this.getFilmHeight()/e}getEffectiveFOV(){return Sh*2*Math.atan(Math.tan(Ml*.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(e,n,i){Wi.set(-1,-1,.5).applyMatrix4(this.projectionMatrixInverse),n.set(Wi.x,Wi.y).multiplyScalar(-e/Wi.z),Wi.set(1,1,.5).applyMatrix4(this.projectionMatrixInverse),i.set(Wi.x,Wi.y).multiplyScalar(-e/Wi.z)}getViewSize(e,n){return this.getViewBounds(e,fm,pm),n.subVectors(pm,fm)}setViewOffset(e,n,i,r,s,o){this.aspect=e/n,this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=n,this.view.offsetX=i,this.view.offsetY=r,this.view.width=s,this.view.height=o,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){const e=this.near;let n=e*Math.tan(Ml*.5*this.fov)/this.zoom,i=2*n,r=this.aspect*i,s=-.5*r;const o=this.view;if(this.view!==null&&this.view.enabled){const l=o.fullWidth,c=o.fullHeight;s+=o.offsetX*r/l,n-=o.offsetY*i/c,r*=o.width/l,i*=o.height/c}const a=this.filmOffset;a!==0&&(s+=e*a/this.getFilmWidth()),this.projectionMatrix.makePerspective(s,s+r,n,n-i,e,this.far,this.coordinateSystem),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){const n=super.toJSON(e);return n.object.fov=this.fov,n.object.zoom=this.zoom,n.object.near=this.near,n.object.far=this.far,n.object.focus=this.focus,n.object.aspect=this.aspect,this.view!==null&&(n.object.view=Object.assign({},this.view)),n.object.filmGauge=this.filmGauge,n.object.filmOffset=this.filmOffset,n}}const ls=-90,cs=1;class mM extends kt{constructor(e,n,i){super(),this.type="CubeCamera",this.renderTarget=i,this.coordinateSystem=null,this.activeMipmapLevel=0;const r=new Fn(ls,cs,e,n);r.layers=this.layers,this.add(r);const s=new Fn(ls,cs,e,n);s.layers=this.layers,this.add(s);const o=new Fn(ls,cs,e,n);o.layers=this.layers,this.add(o);const a=new Fn(ls,cs,e,n);a.layers=this.layers,this.add(a);const l=new Fn(ls,cs,e,n);l.layers=this.layers,this.add(l);const c=new Fn(ls,cs,e,n);c.layers=this.layers,this.add(c)}updateCoordinateSystem(){const e=this.coordinateSystem,n=this.children.concat(),[i,r,s,o,a,l]=n;for(const c of n)this.remove(c);if(e===bi)i.up.set(0,1,0),i.lookAt(1,0,0),r.up.set(0,1,0),r.lookAt(-1,0,0),s.up.set(0,0,-1),s.lookAt(0,1,0),o.up.set(0,0,1),o.lookAt(0,-1,0),a.up.set(0,1,0),a.lookAt(0,0,1),l.up.set(0,1,0),l.lookAt(0,0,-1);else if(e===Zl)i.up.set(0,-1,0),i.lookAt(-1,0,0),r.up.set(0,-1,0),r.lookAt(1,0,0),s.up.set(0,0,1),s.lookAt(0,1,0),o.up.set(0,0,-1),o.lookAt(0,-1,0),a.up.set(0,-1,0),a.lookAt(0,0,1),l.up.set(0,-1,0),l.lookAt(0,0,-1);else throw new Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+e);for(const c of n)this.add(c),c.updateMatrixWorld()}update(e,n){this.parent===null&&this.updateMatrixWorld();const{renderTarget:i,activeMipmapLevel:r}=this;this.coordinateSystem!==e.coordinateSystem&&(this.coordinateSystem=e.coordinateSystem,this.updateCoordinateSystem());const[s,o,a,l,c,d]=this.children,h=e.getRenderTarget(),f=e.getActiveCubeFace(),p=e.getActiveMipmapLevel(),g=e.xr.enabled;e.xr.enabled=!1;const x=i.texture.generateMipmaps;i.texture.generateMipmaps=!1,e.setRenderTarget(i,0,r),e.render(n,s),e.setRenderTarget(i,1,r),e.render(n,o),e.setRenderTarget(i,2,r),e.render(n,a),e.setRenderTarget(i,3,r),e.render(n,l),e.setRenderTarget(i,4,r),e.render(n,c),i.texture.generateMipmaps=x,e.setRenderTarget(i,5,r),e.render(n,d),e.setRenderTarget(h,f,p),e.xr.enabled=g,i.texture.needsPMREMUpdate=!0}}class $v extends _n{constructor(e,n,i,r,s,o,a,l,c,d){e=e!==void 0?e:[],n=n!==void 0?n:Ws,super(e,n,i,r,s,o,a,l,c,d),this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(e){this.image=e}}class gM extends Gr{constructor(e=1,n={}){super(e,e,n),this.isWebGLCubeRenderTarget=!0;const i={width:e,height:e,depth:1},r=[i,i,i,i,i,i];this.texture=new $v(r,n.mapping,n.wrapS,n.wrapT,n.magFilter,n.minFilter,n.format,n.type,n.anisotropy,n.colorSpace),this.texture.isRenderTargetTexture=!0,this.texture.generateMipmaps=n.generateMipmaps!==void 0?n.generateMipmaps:!1,this.texture.minFilter=n.minFilter!==void 0?n.minFilter:li}fromEquirectangularTexture(e,n){this.texture.type=n.type,this.texture.colorSpace=n.colorSpace,this.texture.generateMipmaps=n.generateMipmaps,this.texture.minFilter=n.minFilter,this.texture.magFilter=n.magFilter;const i={uniforms:{tEquirect:{value:null}},vertexShader:`

				varying vec3 vWorldDirection;

				vec3 transformDirection( in vec3 dir, in mat4 matrix ) {

					return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );

				}

				void main() {

					vWorldDirection = transformDirection( position, modelMatrix );

					#include <begin_vertex>
					#include <project_vertex>

				}
			`,fragmentShader:`

				uniform sampler2D tEquirect;

				varying vec3 vWorldDirection;

				#include <common>

				void main() {

					vec3 direction = normalize( vWorldDirection );

					vec2 sampleUV = equirectUv( direction );

					gl_FragColor = texture2D( tEquirect, sampleUV );

				}
			`},r=new ca(5,5,5),s=new fr({name:"CubemapFromEquirect",uniforms:Ks(i.uniforms),vertexShader:i.vertexShader,fragmentShader:i.fragmentShader,side:gn,blending:lr});s.uniforms.tEquirect.value=n;const o=new Tn(r,s),a=n.minFilter;return n.minFilter===Ir&&(n.minFilter=li),new mM(1,10,this).update(e,o),n.minFilter=a,o.geometry.dispose(),o.material.dispose(),this}clear(e,n,i,r){const s=e.getRenderTarget();for(let o=0;o<6;o++)e.setRenderTarget(this,o),e.clear(n,i,r);e.setRenderTarget(s)}}class _M extends kt{constructor(){super(),this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new hi,this.environmentIntensity=1,this.environmentRotation=new hi,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(e,n){return super.copy(e,n),e.background!==null&&(this.background=e.background.clone()),e.environment!==null&&(this.environment=e.environment.clone()),e.fog!==null&&(this.fog=e.fog.clone()),this.backgroundBlurriness=e.backgroundBlurriness,this.backgroundIntensity=e.backgroundIntensity,this.backgroundRotation.copy(e.backgroundRotation),this.environmentIntensity=e.environmentIntensity,this.environmentRotation.copy(e.environmentRotation),e.overrideMaterial!==null&&(this.overrideMaterial=e.overrideMaterial.clone()),this.matrixAutoUpdate=e.matrixAutoUpdate,this}toJSON(e){const n=super.toJSON(e);return this.fog!==null&&(n.object.fog=this.fog.toJSON()),this.backgroundBlurriness>0&&(n.object.backgroundBlurriness=this.backgroundBlurriness),this.backgroundIntensity!==1&&(n.object.backgroundIntensity=this.backgroundIntensity),n.object.backgroundRotation=this.backgroundRotation.toArray(),this.environmentIntensity!==1&&(n.object.environmentIntensity=this.environmentIntensity),n.object.environmentRotation=this.environmentRotation.toArray(),n}}const Eu=new O,vM=new O,xM=new Ze;class Yi{constructor(e=new O(1,0,0),n=0){this.isPlane=!0,this.normal=e,this.constant=n}set(e,n){return this.normal.copy(e),this.constant=n,this}setComponents(e,n,i,r){return this.normal.set(e,n,i),this.constant=r,this}setFromNormalAndCoplanarPoint(e,n){return this.normal.copy(e),this.constant=-n.dot(this.normal),this}setFromCoplanarPoints(e,n,i){const r=Eu.subVectors(i,n).cross(vM.subVectors(e,n)).normalize();return this.setFromNormalAndCoplanarPoint(r,e),this}copy(e){return this.normal.copy(e.normal),this.constant=e.constant,this}normalize(){const e=1/this.normal.length();return this.normal.multiplyScalar(e),this.constant*=e,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(e){return this.normal.dot(e)+this.constant}distanceToSphere(e){return this.distanceToPoint(e.center)-e.radius}projectPoint(e,n){return n.copy(e).addScaledVector(this.normal,-this.distanceToPoint(e))}intersectLine(e,n){const i=e.delta(Eu),r=this.normal.dot(i);if(r===0)return this.distanceToPoint(e.start)===0?n.copy(e.start):null;const s=-(e.start.dot(this.normal)+this.constant)/r;return s<0||s>1?null:n.copy(e.start).addScaledVector(i,s)}intersectsLine(e){const n=this.distanceToPoint(e.start),i=this.distanceToPoint(e.end);return n<0&&i>0||i<0&&n>0}intersectsBox(e){return e.intersectsPlane(this)}intersectsSphere(e){return e.intersectsPlane(this)}coplanarPoint(e){return e.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(e,n){const i=n||xM.getNormalMatrix(e),r=this.coplanarPoint(Eu).applyMatrix4(e),s=this.normal.applyMatrix3(i).normalize();return this.constant=-r.dot(s),this}translate(e){return this.constant-=e.dot(this.normal),this}equals(e){return e.normal.equals(this.normal)&&e.constant===this.constant}clone(){return new this.constructor().copy(this)}}const Mr=new Sc,Ya=new O;class bf{constructor(e=new Yi,n=new Yi,i=new Yi,r=new Yi,s=new Yi,o=new Yi){this.planes=[e,n,i,r,s,o]}set(e,n,i,r,s,o){const a=this.planes;return a[0].copy(e),a[1].copy(n),a[2].copy(i),a[3].copy(r),a[4].copy(s),a[5].copy(o),this}copy(e){const n=this.planes;for(let i=0;i<6;i++)n[i].copy(e.planes[i]);return this}setFromProjectionMatrix(e,n=bi){const i=this.planes,r=e.elements,s=r[0],o=r[1],a=r[2],l=r[3],c=r[4],d=r[5],h=r[6],f=r[7],p=r[8],g=r[9],x=r[10],m=r[11],u=r[12],_=r[13],v=r[14],M=r[15];if(i[0].setComponents(l-s,f-c,m-p,M-u).normalize(),i[1].setComponents(l+s,f+c,m+p,M+u).normalize(),i[2].setComponents(l+o,f+d,m+g,M+_).normalize(),i[3].setComponents(l-o,f-d,m-g,M-_).normalize(),i[4].setComponents(l-a,f-h,m-x,M-v).normalize(),n===bi)i[5].setComponents(l+a,f+h,m+x,M+v).normalize();else if(n===Zl)i[5].setComponents(a,h,x,v).normalize();else throw new Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+n);return this}intersectsObject(e){if(e.boundingSphere!==void 0)e.boundingSphere===null&&e.computeBoundingSphere(),Mr.copy(e.boundingSphere).applyMatrix4(e.matrixWorld);else{const n=e.geometry;n.boundingSphere===null&&n.computeBoundingSphere(),Mr.copy(n.boundingSphere).applyMatrix4(e.matrixWorld)}return this.intersectsSphere(Mr)}intersectsSprite(e){return Mr.center.set(0,0,0),Mr.radius=.7071067811865476,Mr.applyMatrix4(e.matrixWorld),this.intersectsSphere(Mr)}intersectsSphere(e){const n=this.planes,i=e.center,r=-e.radius;for(let s=0;s<6;s++)if(n[s].distanceToPoint(i)<r)return!1;return!0}intersectsBox(e){const n=this.planes;for(let i=0;i<6;i++){const r=n[i];if(Ya.x=r.normal.x>0?e.max.x:e.min.x,Ya.y=r.normal.y>0?e.max.y:e.min.y,Ya.z=r.normal.z>0?e.max.z:e.min.z,r.distanceToPoint(Ya)<0)return!1}return!0}containsPoint(e){const n=this.planes;for(let i=0;i<6;i++)if(n[i].distanceToPoint(e)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}}class El extends eo{constructor(e){super(),this.isLineBasicMaterial=!0,this.type="LineBasicMaterial",this.color=new ct(16777215),this.map=null,this.linewidth=1,this.linecap="round",this.linejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.linewidth=e.linewidth,this.linecap=e.linecap,this.linejoin=e.linejoin,this.fog=e.fog,this}}const Ql=new O,ec=new O,mm=new mt,_o=new Mc,qa=new Sc,wu=new O,gm=new O;class Tu extends kt{constructor(e=new Cn,n=new El){super(),this.isLine=!0,this.type="Line",this.geometry=e,this.material=n,this.updateMorphTargets()}copy(e,n){return super.copy(e,n),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}computeLineDistances(){const e=this.geometry;if(e.index===null){const n=e.attributes.position,i=[0];for(let r=1,s=n.count;r<s;r++)Ql.fromBufferAttribute(n,r-1),ec.fromBufferAttribute(n,r),i[r]=i[r-1],i[r]+=Ql.distanceTo(ec);e.setAttribute("lineDistance",new vn(i,1))}else console.warn("THREE.Line.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}raycast(e,n){const i=this.geometry,r=this.matrixWorld,s=e.params.Line.threshold,o=i.drawRange;if(i.boundingSphere===null&&i.computeBoundingSphere(),qa.copy(i.boundingSphere),qa.applyMatrix4(r),qa.radius+=s,e.ray.intersectsSphere(qa)===!1)return;mm.copy(r).invert(),_o.copy(e.ray).applyMatrix4(mm);const a=s/((this.scale.x+this.scale.y+this.scale.z)/3),l=a*a,c=this.isLineSegments?2:1,d=i.index,f=i.attributes.position;if(d!==null){const p=Math.max(0,o.start),g=Math.min(d.count,o.start+o.count);for(let x=p,m=g-1;x<m;x+=c){const u=d.getX(x),_=d.getX(x+1),v=Ka(this,e,_o,l,u,_);v&&n.push(v)}if(this.isLineLoop){const x=d.getX(g-1),m=d.getX(p),u=Ka(this,e,_o,l,x,m);u&&n.push(u)}}else{const p=Math.max(0,o.start),g=Math.min(f.count,o.start+o.count);for(let x=p,m=g-1;x<m;x+=c){const u=Ka(this,e,_o,l,x,x+1);u&&n.push(u)}if(this.isLineLoop){const x=Ka(this,e,_o,l,g-1,p);x&&n.push(x)}}}updateMorphTargets(){const n=this.geometry.morphAttributes,i=Object.keys(n);if(i.length>0){const r=n[i[0]];if(r!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,o=r.length;s<o;s++){const a=r[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[a]=s}}}}}function Ka(t,e,n,i,r,s){const o=t.geometry.attributes.position;if(Ql.fromBufferAttribute(o,r),ec.fromBufferAttribute(o,s),n.distanceSqToSegment(Ql,ec,wu,gm)>i)return;wu.applyMatrix4(t.matrixWorld);const l=e.ray.origin.distanceTo(wu);if(!(l<e.near||l>e.far))return{distance:l,point:gm.clone().applyMatrix4(t.matrixWorld),index:r,face:null,faceIndex:null,barycoord:null,object:t}}class Za extends kt{constructor(){super(),this.isGroup=!0,this.type="Group"}}class Yv extends _n{constructor(e,n,i,r,s,o,a,l,c,d=Us){if(d!==Us&&d!==Ys)throw new Error("DepthTexture format must be either THREE.DepthFormat or THREE.DepthStencilFormat");i===void 0&&d===Us&&(i=Vr),i===void 0&&d===Ys&&(i=$s),super(null,r,s,o,a,l,d,i,c),this.isDepthTexture=!0,this.image={width:e,height:n},this.magFilter=a!==void 0?a:ni,this.minFilter=l!==void 0?l:ni,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(e){return super.copy(e),this.compareFunction=e.compareFunction,this}toJSON(e){const n=super.toJSON(e);return this.compareFunction!==null&&(n.compareFunction=this.compareFunction),n}}class Fi{constructor(){this.type="Curve",this.arcLengthDivisions=200}getPoint(){return console.warn("THREE.Curve: .getPoint() not implemented."),null}getPointAt(e,n){const i=this.getUtoTmapping(e);return this.getPoint(i,n)}getPoints(e=5){const n=[];for(let i=0;i<=e;i++)n.push(this.getPoint(i/e));return n}getSpacedPoints(e=5){const n=[];for(let i=0;i<=e;i++)n.push(this.getPointAt(i/e));return n}getLength(){const e=this.getLengths();return e[e.length-1]}getLengths(e=this.arcLengthDivisions){if(this.cacheArcLengths&&this.cacheArcLengths.length===e+1&&!this.needsUpdate)return this.cacheArcLengths;this.needsUpdate=!1;const n=[];let i,r=this.getPoint(0),s=0;n.push(0);for(let o=1;o<=e;o++)i=this.getPoint(o/e),s+=i.distanceTo(r),n.push(s),r=i;return this.cacheArcLengths=n,n}updateArcLengths(){this.needsUpdate=!0,this.getLengths()}getUtoTmapping(e,n){const i=this.getLengths();let r=0;const s=i.length;let o;n?o=n:o=e*i[s-1];let a=0,l=s-1,c;for(;a<=l;)if(r=Math.floor(a+(l-a)/2),c=i[r]-o,c<0)a=r+1;else if(c>0)l=r-1;else{l=r;break}if(r=l,i[r]===o)return r/(s-1);const d=i[r],f=i[r+1]-d,p=(o-d)/f;return(r+p)/(s-1)}getTangent(e,n){let r=e-1e-4,s=e+1e-4;r<0&&(r=0),s>1&&(s=1);const o=this.getPoint(r),a=this.getPoint(s),l=n||(o.isVector2?new Fe:new O);return l.copy(a).sub(o).normalize(),l}getTangentAt(e,n){const i=this.getUtoTmapping(e);return this.getTangent(i,n)}computeFrenetFrames(e,n){const i=new O,r=[],s=[],o=[],a=new O,l=new mt;for(let p=0;p<=e;p++){const g=p/e;r[p]=this.getTangentAt(g,new O)}s[0]=new O,o[0]=new O;let c=Number.MAX_VALUE;const d=Math.abs(r[0].x),h=Math.abs(r[0].y),f=Math.abs(r[0].z);d<=c&&(c=d,i.set(1,0,0)),h<=c&&(c=h,i.set(0,1,0)),f<=c&&i.set(0,0,1),a.crossVectors(r[0],i).normalize(),s[0].crossVectors(r[0],a),o[0].crossVectors(r[0],s[0]);for(let p=1;p<=e;p++){if(s[p]=s[p-1].clone(),o[p]=o[p-1].clone(),a.crossVectors(r[p-1],r[p]),a.length()>Number.EPSILON){a.normalize();const g=Math.acos(et(r[p-1].dot(r[p]),-1,1));s[p].applyMatrix4(l.makeRotationAxis(a,g))}o[p].crossVectors(r[p],s[p])}if(n===!0){let p=Math.acos(et(s[0].dot(s[e]),-1,1));p/=e,r[0].dot(a.crossVectors(s[0],s[e]))>0&&(p=-p);for(let g=1;g<=e;g++)s[g].applyMatrix4(l.makeRotationAxis(r[g],p*g)),o[g].crossVectors(r[g],s[g])}return{tangents:r,normals:s,binormals:o}}clone(){return new this.constructor().copy(this)}copy(e){return this.arcLengthDivisions=e.arcLengthDivisions,this}toJSON(){const e={metadata:{version:4.6,type:"Curve",generator:"Curve.toJSON"}};return e.arcLengthDivisions=this.arcLengthDivisions,e.type=this.type,e}fromJSON(e){return this.arcLengthDivisions=e.arcLengthDivisions,this}}class qv extends Fi{constructor(e=0,n=0,i=1,r=1,s=0,o=Math.PI*2,a=!1,l=0){super(),this.isEllipseCurve=!0,this.type="EllipseCurve",this.aX=e,this.aY=n,this.xRadius=i,this.yRadius=r,this.aStartAngle=s,this.aEndAngle=o,this.aClockwise=a,this.aRotation=l}getPoint(e,n=new Fe){const i=n,r=Math.PI*2;let s=this.aEndAngle-this.aStartAngle;const o=Math.abs(s)<Number.EPSILON;for(;s<0;)s+=r;for(;s>r;)s-=r;s<Number.EPSILON&&(o?s=0:s=r),this.aClockwise===!0&&!o&&(s===r?s=-r:s=s-r);const a=this.aStartAngle+e*s;let l=this.aX+this.xRadius*Math.cos(a),c=this.aY+this.yRadius*Math.sin(a);if(this.aRotation!==0){const d=Math.cos(this.aRotation),h=Math.sin(this.aRotation),f=l-this.aX,p=c-this.aY;l=f*d-p*h+this.aX,c=f*h+p*d+this.aY}return i.set(l,c)}copy(e){return super.copy(e),this.aX=e.aX,this.aY=e.aY,this.xRadius=e.xRadius,this.yRadius=e.yRadius,this.aStartAngle=e.aStartAngle,this.aEndAngle=e.aEndAngle,this.aClockwise=e.aClockwise,this.aRotation=e.aRotation,this}toJSON(){const e=super.toJSON();return e.aX=this.aX,e.aY=this.aY,e.xRadius=this.xRadius,e.yRadius=this.yRadius,e.aStartAngle=this.aStartAngle,e.aEndAngle=this.aEndAngle,e.aClockwise=this.aClockwise,e.aRotation=this.aRotation,e}fromJSON(e){return super.fromJSON(e),this.aX=e.aX,this.aY=e.aY,this.xRadius=e.xRadius,this.yRadius=e.yRadius,this.aStartAngle=e.aStartAngle,this.aEndAngle=e.aEndAngle,this.aClockwise=e.aClockwise,this.aRotation=e.aRotation,this}}class yM extends qv{constructor(e,n,i,r,s,o){super(e,n,i,i,r,s,o),this.isArcCurve=!0,this.type="ArcCurve"}}function Rf(){let t=0,e=0,n=0,i=0;function r(s,o,a,l){t=s,e=a,n=-3*s+3*o-2*a-l,i=2*s-2*o+a+l}return{initCatmullRom:function(s,o,a,l,c){r(o,a,c*(a-s),c*(l-o))},initNonuniformCatmullRom:function(s,o,a,l,c,d,h){let f=(o-s)/c-(a-s)/(c+d)+(a-o)/d,p=(a-o)/d-(l-o)/(d+h)+(l-a)/h;f*=d,p*=d,r(o,a,f,p)},calc:function(s){const o=s*s,a=o*s;return t+e*s+n*o+i*a}}}const Ja=new O,Au=new Rf,Cu=new Rf,bu=new Rf;class Kv extends Fi{constructor(e=[],n=!1,i="centripetal",r=.5){super(),this.isCatmullRomCurve3=!0,this.type="CatmullRomCurve3",this.points=e,this.closed=n,this.curveType=i,this.tension=r}getPoint(e,n=new O){const i=n,r=this.points,s=r.length,o=(s-(this.closed?0:1))*e;let a=Math.floor(o),l=o-a;this.closed?a+=a>0?0:(Math.floor(Math.abs(a)/s)+1)*s:l===0&&a===s-1&&(a=s-2,l=1);let c,d;this.closed||a>0?c=r[(a-1)%s]:(Ja.subVectors(r[0],r[1]).add(r[0]),c=Ja);const h=r[a%s],f=r[(a+1)%s];if(this.closed||a+2<s?d=r[(a+2)%s]:(Ja.subVectors(r[s-1],r[s-2]).add(r[s-1]),d=Ja),this.curveType==="centripetal"||this.curveType==="chordal"){const p=this.curveType==="chordal"?.5:.25;let g=Math.pow(c.distanceToSquared(h),p),x=Math.pow(h.distanceToSquared(f),p),m=Math.pow(f.distanceToSquared(d),p);x<1e-4&&(x=1),g<1e-4&&(g=x),m<1e-4&&(m=x),Au.initNonuniformCatmullRom(c.x,h.x,f.x,d.x,g,x,m),Cu.initNonuniformCatmullRom(c.y,h.y,f.y,d.y,g,x,m),bu.initNonuniformCatmullRom(c.z,h.z,f.z,d.z,g,x,m)}else this.curveType==="catmullrom"&&(Au.initCatmullRom(c.x,h.x,f.x,d.x,this.tension),Cu.initCatmullRom(c.y,h.y,f.y,d.y,this.tension),bu.initCatmullRom(c.z,h.z,f.z,d.z,this.tension));return i.set(Au.calc(l),Cu.calc(l),bu.calc(l)),i}copy(e){super.copy(e),this.points=[];for(let n=0,i=e.points.length;n<i;n++){const r=e.points[n];this.points.push(r.clone())}return this.closed=e.closed,this.curveType=e.curveType,this.tension=e.tension,this}toJSON(){const e=super.toJSON();e.points=[];for(let n=0,i=this.points.length;n<i;n++){const r=this.points[n];e.points.push(r.toArray())}return e.closed=this.closed,e.curveType=this.curveType,e.tension=this.tension,e}fromJSON(e){super.fromJSON(e),this.points=[];for(let n=0,i=e.points.length;n<i;n++){const r=e.points[n];this.points.push(new O().fromArray(r))}return this.closed=e.closed,this.curveType=e.curveType,this.tension=e.tension,this}}function _m(t,e,n,i,r){const s=(i-e)*.5,o=(r-n)*.5,a=t*t,l=t*a;return(2*n-2*i+s+o)*l+(-3*n+3*i-2*s-o)*a+s*t+n}function SM(t,e){const n=1-t;return n*n*e}function MM(t,e){return 2*(1-t)*t*e}function EM(t,e){return t*t*e}function Do(t,e,n,i){return SM(t,e)+MM(t,n)+EM(t,i)}function wM(t,e){const n=1-t;return n*n*n*e}function TM(t,e){const n=1-t;return 3*n*n*t*e}function AM(t,e){return 3*(1-t)*t*t*e}function CM(t,e){return t*t*t*e}function Io(t,e,n,i,r){return wM(t,e)+TM(t,n)+AM(t,i)+CM(t,r)}class bM extends Fi{constructor(e=new Fe,n=new Fe,i=new Fe,r=new Fe){super(),this.isCubicBezierCurve=!0,this.type="CubicBezierCurve",this.v0=e,this.v1=n,this.v2=i,this.v3=r}getPoint(e,n=new Fe){const i=n,r=this.v0,s=this.v1,o=this.v2,a=this.v3;return i.set(Io(e,r.x,s.x,o.x,a.x),Io(e,r.y,s.y,o.y,a.y)),i}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this.v3.copy(e.v3),this}toJSON(){const e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e.v3=this.v3.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this.v3.fromArray(e.v3),this}}class RM extends Fi{constructor(e=new O,n=new O,i=new O,r=new O){super(),this.isCubicBezierCurve3=!0,this.type="CubicBezierCurve3",this.v0=e,this.v1=n,this.v2=i,this.v3=r}getPoint(e,n=new O){const i=n,r=this.v0,s=this.v1,o=this.v2,a=this.v3;return i.set(Io(e,r.x,s.x,o.x,a.x),Io(e,r.y,s.y,o.y,a.y),Io(e,r.z,s.z,o.z,a.z)),i}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this.v3.copy(e.v3),this}toJSON(){const e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e.v3=this.v3.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this.v3.fromArray(e.v3),this}}class PM extends Fi{constructor(e=new Fe,n=new Fe){super(),this.isLineCurve=!0,this.type="LineCurve",this.v1=e,this.v2=n}getPoint(e,n=new Fe){const i=n;return e===1?i.copy(this.v2):(i.copy(this.v2).sub(this.v1),i.multiplyScalar(e).add(this.v1)),i}getPointAt(e,n){return this.getPoint(e,n)}getTangent(e,n=new Fe){return n.subVectors(this.v2,this.v1).normalize()}getTangentAt(e,n){return this.getTangent(e,n)}copy(e){return super.copy(e),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){const e=super.toJSON();return e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}}class LM extends Fi{constructor(e=new O,n=new O){super(),this.isLineCurve3=!0,this.type="LineCurve3",this.v1=e,this.v2=n}getPoint(e,n=new O){const i=n;return e===1?i.copy(this.v2):(i.copy(this.v2).sub(this.v1),i.multiplyScalar(e).add(this.v1)),i}getPointAt(e,n){return this.getPoint(e,n)}getTangent(e,n=new O){return n.subVectors(this.v2,this.v1).normalize()}getTangentAt(e,n){return this.getTangent(e,n)}copy(e){return super.copy(e),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){const e=super.toJSON();return e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}}class NM extends Fi{constructor(e=new Fe,n=new Fe,i=new Fe){super(),this.isQuadraticBezierCurve=!0,this.type="QuadraticBezierCurve",this.v0=e,this.v1=n,this.v2=i}getPoint(e,n=new Fe){const i=n,r=this.v0,s=this.v1,o=this.v2;return i.set(Do(e,r.x,s.x,o.x),Do(e,r.y,s.y,o.y)),i}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){const e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}}class Pf extends Fi{constructor(e=new O,n=new O,i=new O){super(),this.isQuadraticBezierCurve3=!0,this.type="QuadraticBezierCurve3",this.v0=e,this.v1=n,this.v2=i}getPoint(e,n=new O){const i=n,r=this.v0,s=this.v1,o=this.v2;return i.set(Do(e,r.x,s.x,o.x),Do(e,r.y,s.y,o.y),Do(e,r.z,s.z,o.z)),i}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){const e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}}class DM extends Fi{constructor(e=[]){super(),this.isSplineCurve=!0,this.type="SplineCurve",this.points=e}getPoint(e,n=new Fe){const i=n,r=this.points,s=(r.length-1)*e,o=Math.floor(s),a=s-o,l=r[o===0?o:o-1],c=r[o],d=r[o>r.length-2?r.length-1:o+1],h=r[o>r.length-3?r.length-1:o+2];return i.set(_m(a,l.x,c.x,d.x,h.x),_m(a,l.y,c.y,d.y,h.y)),i}copy(e){super.copy(e),this.points=[];for(let n=0,i=e.points.length;n<i;n++){const r=e.points[n];this.points.push(r.clone())}return this}toJSON(){const e=super.toJSON();e.points=[];for(let n=0,i=this.points.length;n<i;n++){const r=this.points[n];e.points.push(r.toArray())}return e}fromJSON(e){super.fromJSON(e),this.points=[];for(let n=0,i=e.points.length;n<i;n++){const r=e.points[n];this.points.push(new Fe().fromArray(r))}return this}}var IM=Object.freeze({__proto__:null,ArcCurve:yM,CatmullRomCurve3:Kv,CubicBezierCurve:bM,CubicBezierCurve3:RM,EllipseCurve:qv,LineCurve:PM,LineCurve3:LM,QuadraticBezierCurve:NM,QuadraticBezierCurve3:Pf,SplineCurve:DM});class Ec extends Cn{constructor(e=1,n=1,i=1,r=1){super(),this.type="PlaneGeometry",this.parameters={width:e,height:n,widthSegments:i,heightSegments:r};const s=e/2,o=n/2,a=Math.floor(i),l=Math.floor(r),c=a+1,d=l+1,h=e/a,f=n/l,p=[],g=[],x=[],m=[];for(let u=0;u<d;u++){const _=u*f-o;for(let v=0;v<c;v++){const M=v*h-s;g.push(M,-_,0),x.push(0,0,1),m.push(v/a),m.push(1-u/l)}}for(let u=0;u<l;u++)for(let _=0;_<a;_++){const v=_+c*u,M=_+c*(u+1),R=_+1+c*(u+1),C=_+1+c*u;p.push(v,M,C),p.push(M,R,C)}this.setIndex(p),this.setAttribute("position",new vn(g,3)),this.setAttribute("normal",new vn(x,3)),this.setAttribute("uv",new vn(m,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new Ec(e.width,e.height,e.widthSegments,e.heightSegments)}}class tc extends Cn{constructor(e=1,n=32,i=16,r=0,s=Math.PI*2,o=0,a=Math.PI){super(),this.type="SphereGeometry",this.parameters={radius:e,widthSegments:n,heightSegments:i,phiStart:r,phiLength:s,thetaStart:o,thetaLength:a},n=Math.max(3,Math.floor(n)),i=Math.max(2,Math.floor(i));const l=Math.min(o+a,Math.PI);let c=0;const d=[],h=new O,f=new O,p=[],g=[],x=[],m=[];for(let u=0;u<=i;u++){const _=[],v=u/i;let M=0;u===0&&o===0?M=.5/n:u===i&&l===Math.PI&&(M=-.5/n);for(let R=0;R<=n;R++){const C=R/n;h.x=-e*Math.cos(r+C*s)*Math.sin(o+v*a),h.y=e*Math.cos(o+v*a),h.z=e*Math.sin(r+C*s)*Math.sin(o+v*a),g.push(h.x,h.y,h.z),f.copy(h).normalize(),x.push(f.x,f.y,f.z),m.push(C+M,1-v),_.push(c++)}d.push(_)}for(let u=0;u<i;u++)for(let _=0;_<n;_++){const v=d[u][_+1],M=d[u][_],R=d[u+1][_],C=d[u+1][_+1];(u!==0||o>0)&&p.push(v,M,C),(u!==i-1||l<Math.PI)&&p.push(M,R,C)}this.setIndex(p),this.setAttribute("position",new vn(g,3)),this.setAttribute("normal",new vn(x,3)),this.setAttribute("uv",new vn(m,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new tc(e.radius,e.widthSegments,e.heightSegments,e.phiStart,e.phiLength,e.thetaStart,e.thetaLength)}}class nc extends Cn{constructor(e=new Pf(new O(-1,-1,0),new O(-1,1,0),new O(1,1,0)),n=64,i=1,r=8,s=!1){super(),this.type="TubeGeometry",this.parameters={path:e,tubularSegments:n,radius:i,radialSegments:r,closed:s};const o=e.computeFrenetFrames(n,s);this.tangents=o.tangents,this.normals=o.normals,this.binormals=o.binormals;const a=new O,l=new O,c=new Fe;let d=new O;const h=[],f=[],p=[],g=[];x(),this.setIndex(g),this.setAttribute("position",new vn(h,3)),this.setAttribute("normal",new vn(f,3)),this.setAttribute("uv",new vn(p,2));function x(){for(let v=0;v<n;v++)m(v);m(s===!1?n:0),_(),u()}function m(v){d=e.getPointAt(v/n,d);const M=o.normals[v],R=o.binormals[v];for(let C=0;C<=r;C++){const A=C/r*Math.PI*2,P=Math.sin(A),E=-Math.cos(A);l.x=E*M.x+P*R.x,l.y=E*M.y+P*R.y,l.z=E*M.z+P*R.z,l.normalize(),f.push(l.x,l.y,l.z),a.x=d.x+i*l.x,a.y=d.y+i*l.y,a.z=d.z+i*l.z,h.push(a.x,a.y,a.z)}}function u(){for(let v=1;v<=n;v++)for(let M=1;M<=r;M++){const R=(r+1)*(v-1)+(M-1),C=(r+1)*v+(M-1),A=(r+1)*v+M,P=(r+1)*(v-1)+M;g.push(R,C,P),g.push(C,A,P)}}function _(){for(let v=0;v<=n;v++)for(let M=0;M<=r;M++)c.x=v/n,c.y=M/r,p.push(c.x,c.y)}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}toJSON(){const e=super.toJSON();return e.path=this.parameters.path.toJSON(),e}static fromJSON(e){return new nc(new IM[e.path.type]().fromJSON(e.path),e.tubularSegments,e.radius,e.radialSegments,e.closed)}}class Qa extends eo{constructor(e){super(),this.isMeshStandardMaterial=!0,this.type="MeshStandardMaterial",this.defines={STANDARD:""},this.color=new ct(16777215),this.roughness=1,this.metalness=0,this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.emissive=new ct(0),this.emissiveIntensity=1,this.emissiveMap=null,this.bumpMap=null,this.bumpScale=1,this.normalMap=null,this.normalMapType=Ov,this.normalScale=new Fe(1,1),this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.roughnessMap=null,this.metalnessMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new hi,this.envMapIntensity=1,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.flatShading=!1,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.defines={STANDARD:""},this.color.copy(e.color),this.roughness=e.roughness,this.metalness=e.metalness,this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.emissive.copy(e.emissive),this.emissiveMap=e.emissiveMap,this.emissiveIntensity=e.emissiveIntensity,this.bumpMap=e.bumpMap,this.bumpScale=e.bumpScale,this.normalMap=e.normalMap,this.normalMapType=e.normalMapType,this.normalScale.copy(e.normalScale),this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.roughnessMap=e.roughnessMap,this.metalnessMap=e.metalnessMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.envMapIntensity=e.envMapIntensity,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.flatShading=e.flatShading,this.fog=e.fog,this}}class UM extends eo{constructor(e){super(),this.isMeshDepthMaterial=!0,this.type="MeshDepthMaterial",this.depthPacking=DS,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(e)}copy(e){return super.copy(e),this.depthPacking=e.depthPacking,this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this}}class OM extends eo{constructor(e){super(),this.isMeshDistanceMaterial=!0,this.type="MeshDistanceMaterial",this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(e)}copy(e){return super.copy(e),this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this}}class Zv extends kt{constructor(e,n=1){super(),this.isLight=!0,this.type="Light",this.color=new ct(e),this.intensity=n}dispose(){}copy(e,n){return super.copy(e,n),this.color.copy(e.color),this.intensity=e.intensity,this}toJSON(e){const n=super.toJSON(e);return n.object.color=this.color.getHex(),n.object.intensity=this.intensity,this.groundColor!==void 0&&(n.object.groundColor=this.groundColor.getHex()),this.distance!==void 0&&(n.object.distance=this.distance),this.angle!==void 0&&(n.object.angle=this.angle),this.decay!==void 0&&(n.object.decay=this.decay),this.penumbra!==void 0&&(n.object.penumbra=this.penumbra),this.shadow!==void 0&&(n.object.shadow=this.shadow.toJSON()),this.target!==void 0&&(n.object.target=this.target.uuid),n}}const Ru=new mt,vm=new O,xm=new O;class FM{constructor(e){this.camera=e,this.intensity=1,this.bias=0,this.normalBias=0,this.radius=1,this.blurSamples=8,this.mapSize=new Fe(512,512),this.map=null,this.mapPass=null,this.matrix=new mt,this.autoUpdate=!0,this.needsUpdate=!1,this._frustum=new bf,this._frameExtents=new Fe(1,1),this._viewportCount=1,this._viewports=[new Rt(0,0,1,1)]}getViewportCount(){return this._viewportCount}getFrustum(){return this._frustum}updateMatrices(e){const n=this.camera,i=this.matrix;vm.setFromMatrixPosition(e.matrixWorld),n.position.copy(vm),xm.setFromMatrixPosition(e.target.matrixWorld),n.lookAt(xm),n.updateMatrixWorld(),Ru.multiplyMatrices(n.projectionMatrix,n.matrixWorldInverse),this._frustum.setFromProjectionMatrix(Ru),i.set(.5,0,0,.5,0,.5,0,.5,0,0,.5,.5,0,0,0,1),i.multiply(Ru)}getViewport(e){return this._viewports[e]}getFrameExtents(){return this._frameExtents}dispose(){this.map&&this.map.dispose(),this.mapPass&&this.mapPass.dispose()}copy(e){return this.camera=e.camera.clone(),this.intensity=e.intensity,this.bias=e.bias,this.radius=e.radius,this.mapSize.copy(e.mapSize),this}clone(){return new this.constructor().copy(this)}toJSON(){const e={};return this.intensity!==1&&(e.intensity=this.intensity),this.bias!==0&&(e.bias=this.bias),this.normalBias!==0&&(e.normalBias=this.normalBias),this.radius!==1&&(e.radius=this.radius),(this.mapSize.x!==512||this.mapSize.y!==512)&&(e.mapSize=this.mapSize.toArray()),e.camera=this.camera.toJSON(!1).object,delete e.camera.matrix,e}}class Jv extends Xv{constructor(e=-1,n=1,i=1,r=-1,s=.1,o=2e3){super(),this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=e,this.right=n,this.top=i,this.bottom=r,this.near=s,this.far=o,this.updateProjectionMatrix()}copy(e,n){return super.copy(e,n),this.left=e.left,this.right=e.right,this.top=e.top,this.bottom=e.bottom,this.near=e.near,this.far=e.far,this.zoom=e.zoom,this.view=e.view===null?null:Object.assign({},e.view),this}setViewOffset(e,n,i,r,s,o){this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=n,this.view.offsetX=i,this.view.offsetY=r,this.view.width=s,this.view.height=o,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){const e=(this.right-this.left)/(2*this.zoom),n=(this.top-this.bottom)/(2*this.zoom),i=(this.right+this.left)/2,r=(this.top+this.bottom)/2;let s=i-e,o=i+e,a=r+n,l=r-n;if(this.view!==null&&this.view.enabled){const c=(this.right-this.left)/this.view.fullWidth/this.zoom,d=(this.top-this.bottom)/this.view.fullHeight/this.zoom;s+=c*this.view.offsetX,o=s+c*this.view.width,a-=d*this.view.offsetY,l=a-d*this.view.height}this.projectionMatrix.makeOrthographic(s,o,a,l,this.near,this.far,this.coordinateSystem),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){const n=super.toJSON(e);return n.object.zoom=this.zoom,n.object.left=this.left,n.object.right=this.right,n.object.top=this.top,n.object.bottom=this.bottom,n.object.near=this.near,n.object.far=this.far,this.view!==null&&(n.object.view=Object.assign({},this.view)),n}}class kM extends FM{constructor(){super(new Jv(-5,5,5,-5,.5,500)),this.isDirectionalLightShadow=!0}}class ym extends Zv{constructor(e,n){super(e,n),this.isDirectionalLight=!0,this.type="DirectionalLight",this.position.copy(kt.DEFAULT_UP),this.updateMatrix(),this.target=new kt,this.shadow=new kM}dispose(){this.shadow.dispose()}copy(e){return super.copy(e),this.target=e.target.clone(),this.shadow=e.shadow.clone(),this}}class BM extends Zv{constructor(e,n){super(e,n),this.isAmbientLight=!0,this.type="AmbientLight"}}class zM extends Fn{constructor(e=[]){super(),this.isArrayCamera=!0,this.cameras=e}}const Sm=new mt;class HM{constructor(e,n,i=0,r=1/0){this.ray=new Mc(e,n),this.near=i,this.far=r,this.camera=null,this.layers=new Cf,this.params={Mesh:{},Line:{threshold:1},LOD:{},Points:{threshold:1},Sprite:{}}}set(e,n){this.ray.set(e,n)}setFromCamera(e,n){n.isPerspectiveCamera?(this.ray.origin.setFromMatrixPosition(n.matrixWorld),this.ray.direction.set(e.x,e.y,.5).unproject(n).sub(this.ray.origin).normalize(),this.camera=n):n.isOrthographicCamera?(this.ray.origin.set(e.x,e.y,(n.near+n.far)/(n.near-n.far)).unproject(n),this.ray.direction.set(0,0,-1).transformDirection(n.matrixWorld),this.camera=n):console.error("THREE.Raycaster: Unsupported camera type: "+n.type)}setFromXRController(e){return Sm.identity().extractRotation(e.matrixWorld),this.ray.origin.setFromMatrixPosition(e.matrixWorld),this.ray.direction.set(0,0,-1).applyMatrix4(Sm),this}intersectObject(e,n=!0,i=[]){return Mh(e,this,i,n),i.sort(Mm),i}intersectObjects(e,n=!0,i=[]){for(let r=0,s=e.length;r<s;r++)Mh(e[r],this,i,n);return i.sort(Mm),i}}function Mm(t,e){return t.distance-e.distance}function Mh(t,e,n,i){let r=!0;if(t.layers.test(e.layers)&&t.raycast(e,n)===!1&&(r=!1),r===!0&&i===!0){const s=t.children;for(let o=0,a=s.length;o<a;o++)Mh(s[o],e,n,!0)}}class Em{constructor(e=1,n=0,i=0){return this.radius=e,this.phi=n,this.theta=i,this}set(e,n,i){return this.radius=e,this.phi=n,this.theta=i,this}copy(e){return this.radius=e.radius,this.phi=e.phi,this.theta=e.theta,this}makeSafe(){return this.phi=et(this.phi,1e-6,Math.PI-1e-6),this}setFromVector3(e){return this.setFromCartesianCoords(e.x,e.y,e.z)}setFromCartesianCoords(e,n,i){return this.radius=Math.sqrt(e*e+n*n+i*i),this.radius===0?(this.theta=0,this.phi=0):(this.theta=Math.atan2(e,i),this.phi=Math.acos(et(n/this.radius,-1,1))),this}clone(){return new this.constructor().copy(this)}}class VM extends $r{constructor(e,n=null){super(),this.object=e,this.domElement=n,this.enabled=!0,this.state=-1,this.keys={},this.mouseButtons={LEFT:null,MIDDLE:null,RIGHT:null},this.touches={ONE:null,TWO:null}}connect(){}disconnect(){}dispose(){}update(){}}function wm(t,e,n,i){const r=GM(i);switch(n){case Rv:return t*e;case Lv:return t*e;case Nv:return t*e*2;case Dv:return t*e/r.components*r.byteLength;case wf:return t*e/r.components*r.byteLength;case Iv:return t*e*2/r.components*r.byteLength;case Tf:return t*e*2/r.components*r.byteLength;case Pv:return t*e*3/r.components*r.byteLength;case Qn:return t*e*4/r.components*r.byteLength;case Af:return t*e*4/r.components*r.byteLength;case _l:case vl:return Math.floor((t+3)/4)*Math.floor((e+3)/4)*8;case xl:case yl:return Math.floor((t+3)/4)*Math.floor((e+3)/4)*16;case Kd:case Jd:return Math.max(t,16)*Math.max(e,8)/4;case qd:case Zd:return Math.max(t,8)*Math.max(e,8)/2;case Qd:case eh:return Math.floor((t+3)/4)*Math.floor((e+3)/4)*8;case th:return Math.floor((t+3)/4)*Math.floor((e+3)/4)*16;case nh:return Math.floor((t+3)/4)*Math.floor((e+3)/4)*16;case ih:return Math.floor((t+4)/5)*Math.floor((e+3)/4)*16;case rh:return Math.floor((t+4)/5)*Math.floor((e+4)/5)*16;case sh:return Math.floor((t+5)/6)*Math.floor((e+4)/5)*16;case oh:return Math.floor((t+5)/6)*Math.floor((e+5)/6)*16;case ah:return Math.floor((t+7)/8)*Math.floor((e+4)/5)*16;case lh:return Math.floor((t+7)/8)*Math.floor((e+5)/6)*16;case ch:return Math.floor((t+7)/8)*Math.floor((e+7)/8)*16;case uh:return Math.floor((t+9)/10)*Math.floor((e+4)/5)*16;case dh:return Math.floor((t+9)/10)*Math.floor((e+5)/6)*16;case hh:return Math.floor((t+9)/10)*Math.floor((e+7)/8)*16;case fh:return Math.floor((t+9)/10)*Math.floor((e+9)/10)*16;case ph:return Math.floor((t+11)/12)*Math.floor((e+9)/10)*16;case mh:return Math.floor((t+11)/12)*Math.floor((e+11)/12)*16;case Sl:case gh:case _h:return Math.ceil(t/4)*Math.ceil(e/4)*16;case Uv:case vh:return Math.ceil(t/4)*Math.ceil(e/4)*8;case xh:case yh:return Math.ceil(t/4)*Math.ceil(e/4)*16}throw new Error(`Unable to determine texture byte length for ${n} format.`)}function GM(t){switch(t){case Ui:case Av:return{byteLength:1,components:1};case ea:case Cv:case oa:return{byteLength:2,components:1};case Mf:case Ef:return{byteLength:2,components:4};case Vr:case Sf:case Ci:return{byteLength:4,components:1};case bv:return{byteLength:4,components:3}}throw new Error(`Unknown texture type ${t}.`)}typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:yf}}));typeof window<"u"&&(window.__THREE__?console.warn("WARNING: Multiple instances of Three.js being imported."):window.__THREE__=yf);/**
 * @license
 * Copyright 2010-2024 Three.js Authors
 * SPDX-License-Identifier: MIT
 */function Qv(){let t=null,e=!1,n=null,i=null;function r(s,o){n(s,o),i=t.requestAnimationFrame(r)}return{start:function(){e!==!0&&n!==null&&(i=t.requestAnimationFrame(r),e=!0)},stop:function(){t.cancelAnimationFrame(i),e=!1},setAnimationLoop:function(s){n=s},setContext:function(s){t=s}}}function jM(t){const e=new WeakMap;function n(a,l){const c=a.array,d=a.usage,h=c.byteLength,f=t.createBuffer();t.bindBuffer(l,f),t.bufferData(l,c,d),a.onUploadCallback();let p;if(c instanceof Float32Array)p=t.FLOAT;else if(c instanceof Uint16Array)a.isFloat16BufferAttribute?p=t.HALF_FLOAT:p=t.UNSIGNED_SHORT;else if(c instanceof Int16Array)p=t.SHORT;else if(c instanceof Uint32Array)p=t.UNSIGNED_INT;else if(c instanceof Int32Array)p=t.INT;else if(c instanceof Int8Array)p=t.BYTE;else if(c instanceof Uint8Array)p=t.UNSIGNED_BYTE;else if(c instanceof Uint8ClampedArray)p=t.UNSIGNED_BYTE;else throw new Error("THREE.WebGLAttributes: Unsupported buffer data format: "+c);return{buffer:f,type:p,bytesPerElement:c.BYTES_PER_ELEMENT,version:a.version,size:h}}function i(a,l,c){const d=l.array,h=l.updateRanges;if(t.bindBuffer(c,a),h.length===0)t.bufferSubData(c,0,d);else{h.sort((p,g)=>p.start-g.start);let f=0;for(let p=1;p<h.length;p++){const g=h[f],x=h[p];x.start<=g.start+g.count+1?g.count=Math.max(g.count,x.start+x.count-g.start):(++f,h[f]=x)}h.length=f+1;for(let p=0,g=h.length;p<g;p++){const x=h[p];t.bufferSubData(c,x.start*d.BYTES_PER_ELEMENT,d,x.start,x.count)}l.clearUpdateRanges()}l.onUploadCallback()}function r(a){return a.isInterleavedBufferAttribute&&(a=a.data),e.get(a)}function s(a){a.isInterleavedBufferAttribute&&(a=a.data);const l=e.get(a);l&&(t.deleteBuffer(l.buffer),e.delete(a))}function o(a,l){if(a.isInterleavedBufferAttribute&&(a=a.data),a.isGLBufferAttribute){const d=e.get(a);(!d||d.version<a.version)&&e.set(a,{buffer:a.buffer,type:a.type,bytesPerElement:a.elementSize,version:a.version});return}const c=e.get(a);if(c===void 0)e.set(a,n(a,l));else if(c.version<a.version){if(c.size!==a.array.byteLength)throw new Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");i(c.buffer,a,l),c.version=a.version}}return{get:r,remove:s,update:o}}var WM=`#ifdef USE_ALPHAHASH
	if ( diffuseColor.a < getAlphaHashThreshold( vPosition ) ) discard;
#endif`,XM=`#ifdef USE_ALPHAHASH
	const float ALPHA_HASH_SCALE = 0.05;
	float hash2D( vec2 value ) {
		return fract( 1.0e4 * sin( 17.0 * value.x + 0.1 * value.y ) * ( 0.1 + abs( sin( 13.0 * value.y + value.x ) ) ) );
	}
	float hash3D( vec3 value ) {
		return hash2D( vec2( hash2D( value.xy ), value.z ) );
	}
	float getAlphaHashThreshold( vec3 position ) {
		float maxDeriv = max(
			length( dFdx( position.xyz ) ),
			length( dFdy( position.xyz ) )
		);
		float pixScale = 1.0 / ( ALPHA_HASH_SCALE * maxDeriv );
		vec2 pixScales = vec2(
			exp2( floor( log2( pixScale ) ) ),
			exp2( ceil( log2( pixScale ) ) )
		);
		vec2 alpha = vec2(
			hash3D( floor( pixScales.x * position.xyz ) ),
			hash3D( floor( pixScales.y * position.xyz ) )
		);
		float lerpFactor = fract( log2( pixScale ) );
		float x = ( 1.0 - lerpFactor ) * alpha.x + lerpFactor * alpha.y;
		float a = min( lerpFactor, 1.0 - lerpFactor );
		vec3 cases = vec3(
			x * x / ( 2.0 * a * ( 1.0 - a ) ),
			( x - 0.5 * a ) / ( 1.0 - a ),
			1.0 - ( ( 1.0 - x ) * ( 1.0 - x ) / ( 2.0 * a * ( 1.0 - a ) ) )
		);
		float threshold = ( x < ( 1.0 - a ) )
			? ( ( x < a ) ? cases.x : cases.y )
			: cases.z;
		return clamp( threshold , 1.0e-6, 1.0 );
	}
#endif`,$M=`#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vAlphaMapUv ).g;
#endif`,YM=`#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,qM=`#ifdef USE_ALPHATEST
	#ifdef ALPHA_TO_COVERAGE
	diffuseColor.a = smoothstep( alphaTest, alphaTest + fwidth( diffuseColor.a ), diffuseColor.a );
	if ( diffuseColor.a == 0.0 ) discard;
	#else
	if ( diffuseColor.a < alphaTest ) discard;
	#endif
#endif`,KM=`#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`,ZM=`#ifdef USE_AOMAP
	float ambientOcclusion = ( texture2D( aoMap, vAoMapUv ).r - 1.0 ) * aoMapIntensity + 1.0;
	reflectedLight.indirectDiffuse *= ambientOcclusion;
	#if defined( USE_CLEARCOAT ) 
		clearcoatSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_SHEEN ) 
		sheenSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD )
		float dotNV = saturate( dot( geometryNormal, geometryViewDir ) );
		reflectedLight.indirectSpecular *= computeSpecularOcclusion( dotNV, ambientOcclusion, material.roughness );
	#endif
#endif`,JM=`#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`,QM=`#ifdef USE_BATCHING
	#if ! defined( GL_ANGLE_multi_draw )
	#define gl_DrawID _gl_DrawID
	uniform int _gl_DrawID;
	#endif
	uniform highp sampler2D batchingTexture;
	uniform highp usampler2D batchingIdTexture;
	mat4 getBatchingMatrix( const in float i ) {
		int size = textureSize( batchingTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( batchingTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( batchingTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( batchingTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( batchingTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
	float getIndirectIndex( const in int i ) {
		int size = textureSize( batchingIdTexture, 0 ).x;
		int x = i % size;
		int y = i / size;
		return float( texelFetch( batchingIdTexture, ivec2( x, y ), 0 ).r );
	}
#endif
#ifdef USE_BATCHING_COLOR
	uniform sampler2D batchingColorTexture;
	vec3 getBatchingColor( const in float i ) {
		int size = textureSize( batchingColorTexture, 0 ).x;
		int j = int( i );
		int x = j % size;
		int y = j / size;
		return texelFetch( batchingColorTexture, ivec2( x, y ), 0 ).rgb;
	}
#endif`,eE=`#ifdef USE_BATCHING
	mat4 batchingMatrix = getBatchingMatrix( getIndirectIndex( gl_DrawID ) );
#endif`,tE=`vec3 transformed = vec3( position );
#ifdef USE_ALPHAHASH
	vPosition = vec3( position );
#endif`,nE=`vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`,iE=`float G_BlinnPhong_Implicit( ) {
	return 0.25;
}
float D_BlinnPhong( const in float shininess, const in float dotNH ) {
	return RECIPROCAL_PI * ( shininess * 0.5 + 1.0 ) * pow( dotNH, shininess );
}
vec3 BRDF_BlinnPhong( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in vec3 specularColor, const in float shininess ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( specularColor, 1.0, dotVH );
	float G = G_BlinnPhong_Implicit( );
	float D = D_BlinnPhong( shininess, dotNH );
	return F * ( G * D );
} // validated`,rE=`#ifdef USE_IRIDESCENCE
	const mat3 XYZ_TO_REC709 = mat3(
		 3.2404542, -0.9692660,  0.0556434,
		-1.5371385,  1.8760108, -0.2040259,
		-0.4985314,  0.0415560,  1.0572252
	);
	vec3 Fresnel0ToIor( vec3 fresnel0 ) {
		vec3 sqrtF0 = sqrt( fresnel0 );
		return ( vec3( 1.0 ) + sqrtF0 ) / ( vec3( 1.0 ) - sqrtF0 );
	}
	vec3 IorToFresnel0( vec3 transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - vec3( incidentIor ) ) / ( transmittedIor + vec3( incidentIor ) ) );
	}
	float IorToFresnel0( float transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - incidentIor ) / ( transmittedIor + incidentIor ));
	}
	vec3 evalSensitivity( float OPD, vec3 shift ) {
		float phase = 2.0 * PI * OPD * 1.0e-9;
		vec3 val = vec3( 5.4856e-13, 4.4201e-13, 5.2481e-13 );
		vec3 pos = vec3( 1.6810e+06, 1.7953e+06, 2.2084e+06 );
		vec3 var = vec3( 4.3278e+09, 9.3046e+09, 6.6121e+09 );
		vec3 xyz = val * sqrt( 2.0 * PI * var ) * cos( pos * phase + shift ) * exp( - pow2( phase ) * var );
		xyz.x += 9.7470e-14 * sqrt( 2.0 * PI * 4.5282e+09 ) * cos( 2.2399e+06 * phase + shift[ 0 ] ) * exp( - 4.5282e+09 * pow2( phase ) );
		xyz /= 1.0685e-7;
		vec3 rgb = XYZ_TO_REC709 * xyz;
		return rgb;
	}
	vec3 evalIridescence( float outsideIOR, float eta2, float cosTheta1, float thinFilmThickness, vec3 baseF0 ) {
		vec3 I;
		float iridescenceIOR = mix( outsideIOR, eta2, smoothstep( 0.0, 0.03, thinFilmThickness ) );
		float sinTheta2Sq = pow2( outsideIOR / iridescenceIOR ) * ( 1.0 - pow2( cosTheta1 ) );
		float cosTheta2Sq = 1.0 - sinTheta2Sq;
		if ( cosTheta2Sq < 0.0 ) {
			return vec3( 1.0 );
		}
		float cosTheta2 = sqrt( cosTheta2Sq );
		float R0 = IorToFresnel0( iridescenceIOR, outsideIOR );
		float R12 = F_Schlick( R0, 1.0, cosTheta1 );
		float T121 = 1.0 - R12;
		float phi12 = 0.0;
		if ( iridescenceIOR < outsideIOR ) phi12 = PI;
		float phi21 = PI - phi12;
		vec3 baseIOR = Fresnel0ToIor( clamp( baseF0, 0.0, 0.9999 ) );		vec3 R1 = IorToFresnel0( baseIOR, iridescenceIOR );
		vec3 R23 = F_Schlick( R1, 1.0, cosTheta2 );
		vec3 phi23 = vec3( 0.0 );
		if ( baseIOR[ 0 ] < iridescenceIOR ) phi23[ 0 ] = PI;
		if ( baseIOR[ 1 ] < iridescenceIOR ) phi23[ 1 ] = PI;
		if ( baseIOR[ 2 ] < iridescenceIOR ) phi23[ 2 ] = PI;
		float OPD = 2.0 * iridescenceIOR * thinFilmThickness * cosTheta2;
		vec3 phi = vec3( phi21 ) + phi23;
		vec3 R123 = clamp( R12 * R23, 1e-5, 0.9999 );
		vec3 r123 = sqrt( R123 );
		vec3 Rs = pow2( T121 ) * R23 / ( vec3( 1.0 ) - R123 );
		vec3 C0 = R12 + Rs;
		I = C0;
		vec3 Cm = Rs - T121;
		for ( int m = 1; m <= 2; ++ m ) {
			Cm *= r123;
			vec3 Sm = 2.0 * evalSensitivity( float( m ) * OPD, float( m ) * phi );
			I += Cm * Sm;
		}
		return max( I, vec3( 0.0 ) );
	}
#endif`,sE=`#ifdef USE_BUMPMAP
	uniform sampler2D bumpMap;
	uniform float bumpScale;
	vec2 dHdxy_fwd() {
		vec2 dSTdx = dFdx( vBumpMapUv );
		vec2 dSTdy = dFdy( vBumpMapUv );
		float Hll = bumpScale * texture2D( bumpMap, vBumpMapUv ).x;
		float dBx = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdx ).x - Hll;
		float dBy = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdy ).x - Hll;
		return vec2( dBx, dBy );
	}
	vec3 perturbNormalArb( vec3 surf_pos, vec3 surf_norm, vec2 dHdxy, float faceDirection ) {
		vec3 vSigmaX = normalize( dFdx( surf_pos.xyz ) );
		vec3 vSigmaY = normalize( dFdy( surf_pos.xyz ) );
		vec3 vN = surf_norm;
		vec3 R1 = cross( vSigmaY, vN );
		vec3 R2 = cross( vN, vSigmaX );
		float fDet = dot( vSigmaX, R1 ) * faceDirection;
		vec3 vGrad = sign( fDet ) * ( dHdxy.x * R1 + dHdxy.y * R2 );
		return normalize( abs( fDet ) * surf_norm - vGrad );
	}
#endif`,oE=`#if NUM_CLIPPING_PLANES > 0
	vec4 plane;
	#ifdef ALPHA_TO_COVERAGE
		float distanceToPlane, distanceGradient;
		float clipOpacity = 1.0;
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
			distanceGradient = fwidth( distanceToPlane ) / 2.0;
			clipOpacity *= smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			if ( clipOpacity == 0.0 ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			float unionClipOpacity = 1.0;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
				distanceGradient = fwidth( distanceToPlane ) / 2.0;
				unionClipOpacity *= 1.0 - smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			}
			#pragma unroll_loop_end
			clipOpacity *= 1.0 - unionClipOpacity;
		#endif
		diffuseColor.a *= clipOpacity;
		if ( diffuseColor.a == 0.0 ) discard;
	#else
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			if ( dot( vClipPosition, plane.xyz ) > plane.w ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			bool clipped = true;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				clipped = ( dot( vClipPosition, plane.xyz ) > plane.w ) && clipped;
			}
			#pragma unroll_loop_end
			if ( clipped ) discard;
		#endif
	#endif
#endif`,aE=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`,lE=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`,cE=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,uE=`#if defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#elif defined( USE_COLOR )
	diffuseColor.rgb *= vColor;
#endif`,dE=`#if defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#elif defined( USE_COLOR )
	varying vec3 vColor;
#endif`,hE=`#if defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#elif defined( USE_COLOR ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	varying vec3 vColor;
#endif`,fE=`#if defined( USE_COLOR_ALPHA )
	vColor = vec4( 1.0 );
#elif defined( USE_COLOR ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	vColor = vec3( 1.0 );
#endif
#ifdef USE_COLOR
	vColor *= color;
#endif
#ifdef USE_INSTANCING_COLOR
	vColor.xyz *= instanceColor.xyz;
#endif
#ifdef USE_BATCHING_COLOR
	vec3 batchingColor = getBatchingColor( getIndirectIndex( gl_DrawID ) );
	vColor.xyz *= batchingColor.xyz;
#endif`,pE=`#define PI 3.141592653589793
#define PI2 6.283185307179586
#define PI_HALF 1.5707963267948966
#define RECIPROCAL_PI 0.3183098861837907
#define RECIPROCAL_PI2 0.15915494309189535
#define EPSILON 1e-6
#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
#define whiteComplement( a ) ( 1.0 - saturate( a ) )
float pow2( const in float x ) { return x*x; }
vec3 pow2( const in vec3 x ) { return x*x; }
float pow3( const in float x ) { return x*x*x; }
float pow4( const in float x ) { float x2 = x*x; return x2*x2; }
float max3( const in vec3 v ) { return max( max( v.x, v.y ), v.z ); }
float average( const in vec3 v ) { return dot( v, vec3( 0.3333333 ) ); }
highp float rand( const in vec2 uv ) {
	const highp float a = 12.9898, b = 78.233, c = 43758.5453;
	highp float dt = dot( uv.xy, vec2( a,b ) ), sn = mod( dt, PI );
	return fract( sin( sn ) * c );
}
#ifdef HIGH_PRECISION
	float precisionSafeLength( vec3 v ) { return length( v ); }
#else
	float precisionSafeLength( vec3 v ) {
		float maxComponent = max3( abs( v ) );
		return length( v / maxComponent ) * maxComponent;
	}
#endif
struct IncidentLight {
	vec3 color;
	vec3 direction;
	bool visible;
};
struct ReflectedLight {
	vec3 directDiffuse;
	vec3 directSpecular;
	vec3 indirectDiffuse;
	vec3 indirectSpecular;
};
#ifdef USE_ALPHAHASH
	varying vec3 vPosition;
#endif
vec3 transformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );
}
vec3 inverseTransformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( vec4( dir, 0.0 ) * matrix ).xyz );
}
mat3 transposeMat3( const in mat3 m ) {
	mat3 tmp;
	tmp[ 0 ] = vec3( m[ 0 ].x, m[ 1 ].x, m[ 2 ].x );
	tmp[ 1 ] = vec3( m[ 0 ].y, m[ 1 ].y, m[ 2 ].y );
	tmp[ 2 ] = vec3( m[ 0 ].z, m[ 1 ].z, m[ 2 ].z );
	return tmp;
}
bool isPerspectiveMatrix( mat4 m ) {
	return m[ 2 ][ 3 ] == - 1.0;
}
vec2 equirectUv( in vec3 dir ) {
	float u = atan( dir.z, dir.x ) * RECIPROCAL_PI2 + 0.5;
	float v = asin( clamp( dir.y, - 1.0, 1.0 ) ) * RECIPROCAL_PI + 0.5;
	return vec2( u, v );
}
vec3 BRDF_Lambert( const in vec3 diffuseColor ) {
	return RECIPROCAL_PI * diffuseColor;
}
vec3 F_Schlick( const in vec3 f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
}
float F_Schlick( const in float f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
} // validated`,mE=`#ifdef ENVMAP_TYPE_CUBE_UV
	#define cubeUV_minMipLevel 4.0
	#define cubeUV_minTileSize 16.0
	float getFace( vec3 direction ) {
		vec3 absDirection = abs( direction );
		float face = - 1.0;
		if ( absDirection.x > absDirection.z ) {
			if ( absDirection.x > absDirection.y )
				face = direction.x > 0.0 ? 0.0 : 3.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		} else {
			if ( absDirection.z > absDirection.y )
				face = direction.z > 0.0 ? 2.0 : 5.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		}
		return face;
	}
	vec2 getUV( vec3 direction, float face ) {
		vec2 uv;
		if ( face == 0.0 ) {
			uv = vec2( direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 1.0 ) {
			uv = vec2( - direction.x, - direction.z ) / abs( direction.y );
		} else if ( face == 2.0 ) {
			uv = vec2( - direction.x, direction.y ) / abs( direction.z );
		} else if ( face == 3.0 ) {
			uv = vec2( - direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 4.0 ) {
			uv = vec2( - direction.x, direction.z ) / abs( direction.y );
		} else {
			uv = vec2( direction.x, direction.y ) / abs( direction.z );
		}
		return 0.5 * ( uv + 1.0 );
	}
	vec3 bilinearCubeUV( sampler2D envMap, vec3 direction, float mipInt ) {
		float face = getFace( direction );
		float filterInt = max( cubeUV_minMipLevel - mipInt, 0.0 );
		mipInt = max( mipInt, cubeUV_minMipLevel );
		float faceSize = exp2( mipInt );
		highp vec2 uv = getUV( direction, face ) * ( faceSize - 2.0 ) + 1.0;
		if ( face > 2.0 ) {
			uv.y += faceSize;
			face -= 3.0;
		}
		uv.x += face * faceSize;
		uv.x += filterInt * 3.0 * cubeUV_minTileSize;
		uv.y += 4.0 * ( exp2( CUBEUV_MAX_MIP ) - faceSize );
		uv.x *= CUBEUV_TEXEL_WIDTH;
		uv.y *= CUBEUV_TEXEL_HEIGHT;
		#ifdef texture2DGradEXT
			return texture2DGradEXT( envMap, uv, vec2( 0.0 ), vec2( 0.0 ) ).rgb;
		#else
			return texture2D( envMap, uv ).rgb;
		#endif
	}
	#define cubeUV_r0 1.0
	#define cubeUV_m0 - 2.0
	#define cubeUV_r1 0.8
	#define cubeUV_m1 - 1.0
	#define cubeUV_r4 0.4
	#define cubeUV_m4 2.0
	#define cubeUV_r5 0.305
	#define cubeUV_m5 3.0
	#define cubeUV_r6 0.21
	#define cubeUV_m6 4.0
	float roughnessToMip( float roughness ) {
		float mip = 0.0;
		if ( roughness >= cubeUV_r1 ) {
			mip = ( cubeUV_r0 - roughness ) * ( cubeUV_m1 - cubeUV_m0 ) / ( cubeUV_r0 - cubeUV_r1 ) + cubeUV_m0;
		} else if ( roughness >= cubeUV_r4 ) {
			mip = ( cubeUV_r1 - roughness ) * ( cubeUV_m4 - cubeUV_m1 ) / ( cubeUV_r1 - cubeUV_r4 ) + cubeUV_m1;
		} else if ( roughness >= cubeUV_r5 ) {
			mip = ( cubeUV_r4 - roughness ) * ( cubeUV_m5 - cubeUV_m4 ) / ( cubeUV_r4 - cubeUV_r5 ) + cubeUV_m4;
		} else if ( roughness >= cubeUV_r6 ) {
			mip = ( cubeUV_r5 - roughness ) * ( cubeUV_m6 - cubeUV_m5 ) / ( cubeUV_r5 - cubeUV_r6 ) + cubeUV_m5;
		} else {
			mip = - 2.0 * log2( 1.16 * roughness );		}
		return mip;
	}
	vec4 textureCubeUV( sampler2D envMap, vec3 sampleDir, float roughness ) {
		float mip = clamp( roughnessToMip( roughness ), cubeUV_m0, CUBEUV_MAX_MIP );
		float mipF = fract( mip );
		float mipInt = floor( mip );
		vec3 color0 = bilinearCubeUV( envMap, sampleDir, mipInt );
		if ( mipF == 0.0 ) {
			return vec4( color0, 1.0 );
		} else {
			vec3 color1 = bilinearCubeUV( envMap, sampleDir, mipInt + 1.0 );
			return vec4( mix( color0, color1, mipF ), 1.0 );
		}
	}
#endif`,gE=`vec3 transformedNormal = objectNormal;
#ifdef USE_TANGENT
	vec3 transformedTangent = objectTangent;
#endif
#ifdef USE_BATCHING
	mat3 bm = mat3( batchingMatrix );
	transformedNormal /= vec3( dot( bm[ 0 ], bm[ 0 ] ), dot( bm[ 1 ], bm[ 1 ] ), dot( bm[ 2 ], bm[ 2 ] ) );
	transformedNormal = bm * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = bm * transformedTangent;
	#endif
#endif
#ifdef USE_INSTANCING
	mat3 im = mat3( instanceMatrix );
	transformedNormal /= vec3( dot( im[ 0 ], im[ 0 ] ), dot( im[ 1 ], im[ 1 ] ), dot( im[ 2 ], im[ 2 ] ) );
	transformedNormal = im * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = im * transformedTangent;
	#endif
#endif
transformedNormal = normalMatrix * transformedNormal;
#ifdef FLIP_SIDED
	transformedNormal = - transformedNormal;
#endif
#ifdef USE_TANGENT
	transformedTangent = ( modelViewMatrix * vec4( transformedTangent, 0.0 ) ).xyz;
	#ifdef FLIP_SIDED
		transformedTangent = - transformedTangent;
	#endif
#endif`,_E=`#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`,vE=`#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vDisplacementMapUv ).x * displacementScale + displacementBias );
#endif`,xE=`#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vEmissiveMapUv );
	#ifdef DECODE_VIDEO_TEXTURE_EMISSIVE
		emissiveColor = sRGBTransferEOTF( emissiveColor );
	#endif
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`,yE=`#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`,SE="gl_FragColor = linearToOutputTexel( gl_FragColor );",ME=`vec4 LinearTransferOETF( in vec4 value ) {
	return value;
}
vec4 sRGBTransferEOTF( in vec4 value ) {
	return vec4( mix( pow( value.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), value.rgb * 0.0773993808, vec3( lessThanEqual( value.rgb, vec3( 0.04045 ) ) ) ), value.a );
}
vec4 sRGBTransferOETF( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`,EE=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vec3 cameraToFrag;
		if ( isOrthographic ) {
			cameraToFrag = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToFrag = normalize( vWorldPosition - cameraPosition );
		}
		vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vec3 reflectVec = reflect( cameraToFrag, worldNormal );
		#else
			vec3 reflectVec = refract( cameraToFrag, worldNormal, refractionRatio );
		#endif
	#else
		vec3 reflectVec = vReflect;
	#endif
	#ifdef ENVMAP_TYPE_CUBE
		vec4 envColor = textureCube( envMap, envMapRotation * vec3( flipEnvMap * reflectVec.x, reflectVec.yz ) );
	#else
		vec4 envColor = vec4( 0.0 );
	#endif
	#ifdef ENVMAP_BLENDING_MULTIPLY
		outgoingLight = mix( outgoingLight, outgoingLight * envColor.xyz, specularStrength * reflectivity );
	#elif defined( ENVMAP_BLENDING_MIX )
		outgoingLight = mix( outgoingLight, envColor.xyz, specularStrength * reflectivity );
	#elif defined( ENVMAP_BLENDING_ADD )
		outgoingLight += envColor.xyz * specularStrength * reflectivity;
	#endif
#endif`,wE=`#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform float flipEnvMap;
	uniform mat3 envMapRotation;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
	
#endif`,TE=`#ifdef USE_ENVMAP
	uniform float reflectivity;
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		varying vec3 vWorldPosition;
		uniform float refractionRatio;
	#else
		varying vec3 vReflect;
	#endif
#endif`,AE=`#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		
		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`,CE=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vWorldPosition = worldPosition.xyz;
	#else
		vec3 cameraToVertex;
		if ( isOrthographic ) {
			cameraToVertex = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToVertex = normalize( worldPosition.xyz - cameraPosition );
		}
		vec3 worldNormal = inverseTransformDirection( transformedNormal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vReflect = reflect( cameraToVertex, worldNormal );
		#else
			vReflect = refract( cameraToVertex, worldNormal, refractionRatio );
		#endif
	#endif
#endif`,bE=`#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`,RE=`#ifdef USE_FOG
	varying float vFogDepth;
#endif`,PE=`#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`,LE=`#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`,NE=`#ifdef USE_GRADIENTMAP
	uniform sampler2D gradientMap;
#endif
vec3 getGradientIrradiance( vec3 normal, vec3 lightDirection ) {
	float dotNL = dot( normal, lightDirection );
	vec2 coord = vec2( dotNL * 0.5 + 0.5, 0.0 );
	#ifdef USE_GRADIENTMAP
		return vec3( texture2D( gradientMap, coord ).r );
	#else
		vec2 fw = fwidth( coord ) * 0.5;
		return mix( vec3( 0.7 ), vec3( 1.0 ), smoothstep( 0.7 - fw.x, 0.7 + fw.x, coord.x ) );
	#endif
}`,DE=`#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`,IE=`LambertMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularStrength = specularStrength;`,UE=`varying vec3 vViewPosition;
struct LambertMaterial {
	vec3 diffuseColor;
	float specularStrength;
};
void RE_Direct_Lambert( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Lambert( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Lambert
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Lambert`,OE=`uniform bool receiveShadow;
uniform vec3 ambientLightColor;
#if defined( USE_LIGHT_PROBES )
	uniform vec3 lightProbe[ 9 ];
#endif
vec3 shGetIrradianceAt( in vec3 normal, in vec3 shCoefficients[ 9 ] ) {
	float x = normal.x, y = normal.y, z = normal.z;
	vec3 result = shCoefficients[ 0 ] * 0.886227;
	result += shCoefficients[ 1 ] * 2.0 * 0.511664 * y;
	result += shCoefficients[ 2 ] * 2.0 * 0.511664 * z;
	result += shCoefficients[ 3 ] * 2.0 * 0.511664 * x;
	result += shCoefficients[ 4 ] * 2.0 * 0.429043 * x * y;
	result += shCoefficients[ 5 ] * 2.0 * 0.429043 * y * z;
	result += shCoefficients[ 6 ] * ( 0.743125 * z * z - 0.247708 );
	result += shCoefficients[ 7 ] * 2.0 * 0.429043 * x * z;
	result += shCoefficients[ 8 ] * 0.429043 * ( x * x - y * y );
	return result;
}
vec3 getLightProbeIrradiance( const in vec3 lightProbe[ 9 ], const in vec3 normal ) {
	vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
	vec3 irradiance = shGetIrradianceAt( worldNormal, lightProbe );
	return irradiance;
}
vec3 getAmbientLightIrradiance( const in vec3 ambientLightColor ) {
	vec3 irradiance = ambientLightColor;
	return irradiance;
}
float getDistanceAttenuation( const in float lightDistance, const in float cutoffDistance, const in float decayExponent ) {
	float distanceFalloff = 1.0 / max( pow( lightDistance, decayExponent ), 0.01 );
	if ( cutoffDistance > 0.0 ) {
		distanceFalloff *= pow2( saturate( 1.0 - pow4( lightDistance / cutoffDistance ) ) );
	}
	return distanceFalloff;
}
float getSpotAttenuation( const in float coneCosine, const in float penumbraCosine, const in float angleCosine ) {
	return smoothstep( coneCosine, penumbraCosine, angleCosine );
}
#if NUM_DIR_LIGHTS > 0
	struct DirectionalLight {
		vec3 direction;
		vec3 color;
	};
	uniform DirectionalLight directionalLights[ NUM_DIR_LIGHTS ];
	void getDirectionalLightInfo( const in DirectionalLight directionalLight, out IncidentLight light ) {
		light.color = directionalLight.color;
		light.direction = directionalLight.direction;
		light.visible = true;
	}
#endif
#if NUM_POINT_LIGHTS > 0
	struct PointLight {
		vec3 position;
		vec3 color;
		float distance;
		float decay;
	};
	uniform PointLight pointLights[ NUM_POINT_LIGHTS ];
	void getPointLightInfo( const in PointLight pointLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = pointLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float lightDistance = length( lVector );
		light.color = pointLight.color;
		light.color *= getDistanceAttenuation( lightDistance, pointLight.distance, pointLight.decay );
		light.visible = ( light.color != vec3( 0.0 ) );
	}
#endif
#if NUM_SPOT_LIGHTS > 0
	struct SpotLight {
		vec3 position;
		vec3 direction;
		vec3 color;
		float distance;
		float decay;
		float coneCos;
		float penumbraCos;
	};
	uniform SpotLight spotLights[ NUM_SPOT_LIGHTS ];
	void getSpotLightInfo( const in SpotLight spotLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = spotLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float angleCos = dot( light.direction, spotLight.direction );
		float spotAttenuation = getSpotAttenuation( spotLight.coneCos, spotLight.penumbraCos, angleCos );
		if ( spotAttenuation > 0.0 ) {
			float lightDistance = length( lVector );
			light.color = spotLight.color * spotAttenuation;
			light.color *= getDistanceAttenuation( lightDistance, spotLight.distance, spotLight.decay );
			light.visible = ( light.color != vec3( 0.0 ) );
		} else {
			light.color = vec3( 0.0 );
			light.visible = false;
		}
	}
#endif
#if NUM_RECT_AREA_LIGHTS > 0
	struct RectAreaLight {
		vec3 color;
		vec3 position;
		vec3 halfWidth;
		vec3 halfHeight;
	};
	uniform sampler2D ltc_1;	uniform sampler2D ltc_2;
	uniform RectAreaLight rectAreaLights[ NUM_RECT_AREA_LIGHTS ];
#endif
#if NUM_HEMI_LIGHTS > 0
	struct HemisphereLight {
		vec3 direction;
		vec3 skyColor;
		vec3 groundColor;
	};
	uniform HemisphereLight hemisphereLights[ NUM_HEMI_LIGHTS ];
	vec3 getHemisphereLightIrradiance( const in HemisphereLight hemiLight, const in vec3 normal ) {
		float dotNL = dot( normal, hemiLight.direction );
		float hemiDiffuseWeight = 0.5 * dotNL + 0.5;
		vec3 irradiance = mix( hemiLight.groundColor, hemiLight.skyColor, hemiDiffuseWeight );
		return irradiance;
	}
#endif`,FE=`#ifdef USE_ENVMAP
	vec3 getIBLIrradiance( const in vec3 normal ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * worldNormal, 1.0 );
			return PI * envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	vec3 getIBLRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 reflectVec = reflect( - viewDir, normal );
			reflectVec = normalize( mix( reflectVec, normal, roughness * roughness) );
			reflectVec = inverseTransformDirection( reflectVec, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * reflectVec, roughness );
			return envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	#ifdef USE_ANISOTROPY
		vec3 getIBLAnisotropyRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness, const in vec3 bitangent, const in float anisotropy ) {
			#ifdef ENVMAP_TYPE_CUBE_UV
				vec3 bentNormal = cross( bitangent, viewDir );
				bentNormal = normalize( cross( bentNormal, bitangent ) );
				bentNormal = normalize( mix( bentNormal, normal, pow2( pow2( 1.0 - anisotropy * ( 1.0 - roughness ) ) ) ) );
				return getIBLRadiance( viewDir, bentNormal, roughness );
			#else
				return vec3( 0.0 );
			#endif
		}
	#endif
#endif`,kE=`ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`,BE=`varying vec3 vViewPosition;
struct ToonMaterial {
	vec3 diffuseColor;
};
void RE_Direct_Toon( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 irradiance = getGradientIrradiance( geometryNormal, directLight.direction ) * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Toon( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Toon
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon`,zE=`BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`,HE=`varying vec3 vViewPosition;
struct BlinnPhongMaterial {
	vec3 diffuseColor;
	vec3 specularColor;
	float specularShininess;
	float specularStrength;
};
void RE_Direct_BlinnPhong( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
	reflectedLight.directSpecular += irradiance * BRDF_BlinnPhong( directLight.direction, geometryViewDir, geometryNormal, material.specularColor, material.specularShininess ) * material.specularStrength;
}
void RE_IndirectDiffuse_BlinnPhong( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_BlinnPhong
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong`,VE=`PhysicalMaterial material;
material.diffuseColor = diffuseColor.rgb * ( 1.0 - metalnessFactor );
vec3 dxy = max( abs( dFdx( nonPerturbedNormal ) ), abs( dFdy( nonPerturbedNormal ) ) );
float geometryRoughness = max( max( dxy.x, dxy.y ), dxy.z );
material.roughness = max( roughnessFactor, 0.0525 );material.roughness += geometryRoughness;
material.roughness = min( material.roughness, 1.0 );
#ifdef IOR
	material.ior = ior;
	#ifdef USE_SPECULAR
		float specularIntensityFactor = specularIntensity;
		vec3 specularColorFactor = specularColor;
		#ifdef USE_SPECULAR_COLORMAP
			specularColorFactor *= texture2D( specularColorMap, vSpecularColorMapUv ).rgb;
		#endif
		#ifdef USE_SPECULAR_INTENSITYMAP
			specularIntensityFactor *= texture2D( specularIntensityMap, vSpecularIntensityMapUv ).a;
		#endif
		material.specularF90 = mix( specularIntensityFactor, 1.0, metalnessFactor );
	#else
		float specularIntensityFactor = 1.0;
		vec3 specularColorFactor = vec3( 1.0 );
		material.specularF90 = 1.0;
	#endif
	material.specularColor = mix( min( pow2( ( material.ior - 1.0 ) / ( material.ior + 1.0 ) ) * specularColorFactor, vec3( 1.0 ) ) * specularIntensityFactor, diffuseColor.rgb, metalnessFactor );
#else
	material.specularColor = mix( vec3( 0.04 ), diffuseColor.rgb, metalnessFactor );
	material.specularF90 = 1.0;
#endif
#ifdef USE_CLEARCOAT
	material.clearcoat = clearcoat;
	material.clearcoatRoughness = clearcoatRoughness;
	material.clearcoatF0 = vec3( 0.04 );
	material.clearcoatF90 = 1.0;
	#ifdef USE_CLEARCOATMAP
		material.clearcoat *= texture2D( clearcoatMap, vClearcoatMapUv ).x;
	#endif
	#ifdef USE_CLEARCOAT_ROUGHNESSMAP
		material.clearcoatRoughness *= texture2D( clearcoatRoughnessMap, vClearcoatRoughnessMapUv ).y;
	#endif
	material.clearcoat = saturate( material.clearcoat );	material.clearcoatRoughness = max( material.clearcoatRoughness, 0.0525 );
	material.clearcoatRoughness += geometryRoughness;
	material.clearcoatRoughness = min( material.clearcoatRoughness, 1.0 );
#endif
#ifdef USE_DISPERSION
	material.dispersion = dispersion;
#endif
#ifdef USE_IRIDESCENCE
	material.iridescence = iridescence;
	material.iridescenceIOR = iridescenceIOR;
	#ifdef USE_IRIDESCENCEMAP
		material.iridescence *= texture2D( iridescenceMap, vIridescenceMapUv ).r;
	#endif
	#ifdef USE_IRIDESCENCE_THICKNESSMAP
		material.iridescenceThickness = (iridescenceThicknessMaximum - iridescenceThicknessMinimum) * texture2D( iridescenceThicknessMap, vIridescenceThicknessMapUv ).g + iridescenceThicknessMinimum;
	#else
		material.iridescenceThickness = iridescenceThicknessMaximum;
	#endif
#endif
#ifdef USE_SHEEN
	material.sheenColor = sheenColor;
	#ifdef USE_SHEEN_COLORMAP
		material.sheenColor *= texture2D( sheenColorMap, vSheenColorMapUv ).rgb;
	#endif
	material.sheenRoughness = clamp( sheenRoughness, 0.07, 1.0 );
	#ifdef USE_SHEEN_ROUGHNESSMAP
		material.sheenRoughness *= texture2D( sheenRoughnessMap, vSheenRoughnessMapUv ).a;
	#endif
#endif
#ifdef USE_ANISOTROPY
	#ifdef USE_ANISOTROPYMAP
		mat2 anisotropyMat = mat2( anisotropyVector.x, anisotropyVector.y, - anisotropyVector.y, anisotropyVector.x );
		vec3 anisotropyPolar = texture2D( anisotropyMap, vAnisotropyMapUv ).rgb;
		vec2 anisotropyV = anisotropyMat * normalize( 2.0 * anisotropyPolar.rg - vec2( 1.0 ) ) * anisotropyPolar.b;
	#else
		vec2 anisotropyV = anisotropyVector;
	#endif
	material.anisotropy = length( anisotropyV );
	if( material.anisotropy == 0.0 ) {
		anisotropyV = vec2( 1.0, 0.0 );
	} else {
		anisotropyV /= material.anisotropy;
		material.anisotropy = saturate( material.anisotropy );
	}
	material.alphaT = mix( pow2( material.roughness ), 1.0, pow2( material.anisotropy ) );
	material.anisotropyT = tbn[ 0 ] * anisotropyV.x + tbn[ 1 ] * anisotropyV.y;
	material.anisotropyB = tbn[ 1 ] * anisotropyV.x - tbn[ 0 ] * anisotropyV.y;
#endif`,GE=`struct PhysicalMaterial {
	vec3 diffuseColor;
	float roughness;
	vec3 specularColor;
	float specularF90;
	float dispersion;
	#ifdef USE_CLEARCOAT
		float clearcoat;
		float clearcoatRoughness;
		vec3 clearcoatF0;
		float clearcoatF90;
	#endif
	#ifdef USE_IRIDESCENCE
		float iridescence;
		float iridescenceIOR;
		float iridescenceThickness;
		vec3 iridescenceFresnel;
		vec3 iridescenceF0;
	#endif
	#ifdef USE_SHEEN
		vec3 sheenColor;
		float sheenRoughness;
	#endif
	#ifdef IOR
		float ior;
	#endif
	#ifdef USE_TRANSMISSION
		float transmission;
		float transmissionAlpha;
		float thickness;
		float attenuationDistance;
		vec3 attenuationColor;
	#endif
	#ifdef USE_ANISOTROPY
		float anisotropy;
		float alphaT;
		vec3 anisotropyT;
		vec3 anisotropyB;
	#endif
};
vec3 clearcoatSpecularDirect = vec3( 0.0 );
vec3 clearcoatSpecularIndirect = vec3( 0.0 );
vec3 sheenSpecularDirect = vec3( 0.0 );
vec3 sheenSpecularIndirect = vec3(0.0 );
vec3 Schlick_to_F0( const in vec3 f, const in float f90, const in float dotVH ) {
    float x = clamp( 1.0 - dotVH, 0.0, 1.0 );
    float x2 = x * x;
    float x5 = clamp( x * x2 * x2, 0.0, 0.9999 );
    return ( f - vec3( f90 ) * x5 ) / ( 1.0 - x5 );
}
float V_GGX_SmithCorrelated( const in float alpha, const in float dotNL, const in float dotNV ) {
	float a2 = pow2( alpha );
	float gv = dotNL * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNV ) );
	float gl = dotNV * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNL ) );
	return 0.5 / max( gv + gl, EPSILON );
}
float D_GGX( const in float alpha, const in float dotNH ) {
	float a2 = pow2( alpha );
	float denom = pow2( dotNH ) * ( a2 - 1.0 ) + 1.0;
	return RECIPROCAL_PI * a2 / pow2( denom );
}
#ifdef USE_ANISOTROPY
	float V_GGX_SmithCorrelated_Anisotropic( const in float alphaT, const in float alphaB, const in float dotTV, const in float dotBV, const in float dotTL, const in float dotBL, const in float dotNV, const in float dotNL ) {
		float gv = dotNL * length( vec3( alphaT * dotTV, alphaB * dotBV, dotNV ) );
		float gl = dotNV * length( vec3( alphaT * dotTL, alphaB * dotBL, dotNL ) );
		float v = 0.5 / ( gv + gl );
		return saturate(v);
	}
	float D_GGX_Anisotropic( const in float alphaT, const in float alphaB, const in float dotNH, const in float dotTH, const in float dotBH ) {
		float a2 = alphaT * alphaB;
		highp vec3 v = vec3( alphaB * dotTH, alphaT * dotBH, a2 * dotNH );
		highp float v2 = dot( v, v );
		float w2 = a2 / v2;
		return RECIPROCAL_PI * a2 * pow2 ( w2 );
	}
#endif
#ifdef USE_CLEARCOAT
	vec3 BRDF_GGX_Clearcoat( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material) {
		vec3 f0 = material.clearcoatF0;
		float f90 = material.clearcoatF90;
		float roughness = material.clearcoatRoughness;
		float alpha = pow2( roughness );
		vec3 halfDir = normalize( lightDir + viewDir );
		float dotNL = saturate( dot( normal, lightDir ) );
		float dotNV = saturate( dot( normal, viewDir ) );
		float dotNH = saturate( dot( normal, halfDir ) );
		float dotVH = saturate( dot( viewDir, halfDir ) );
		vec3 F = F_Schlick( f0, f90, dotVH );
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
		return F * ( V * D );
	}
#endif
vec3 BRDF_GGX( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material ) {
	vec3 f0 = material.specularColor;
	float f90 = material.specularF90;
	float roughness = material.roughness;
	float alpha = pow2( roughness );
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( f0, f90, dotVH );
	#ifdef USE_IRIDESCENCE
		F = mix( F, material.iridescenceFresnel, material.iridescence );
	#endif
	#ifdef USE_ANISOTROPY
		float dotTL = dot( material.anisotropyT, lightDir );
		float dotTV = dot( material.anisotropyT, viewDir );
		float dotTH = dot( material.anisotropyT, halfDir );
		float dotBL = dot( material.anisotropyB, lightDir );
		float dotBV = dot( material.anisotropyB, viewDir );
		float dotBH = dot( material.anisotropyB, halfDir );
		float V = V_GGX_SmithCorrelated_Anisotropic( material.alphaT, alpha, dotTV, dotBV, dotTL, dotBL, dotNV, dotNL );
		float D = D_GGX_Anisotropic( material.alphaT, alpha, dotNH, dotTH, dotBH );
	#else
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
	#endif
	return F * ( V * D );
}
vec2 LTC_Uv( const in vec3 N, const in vec3 V, const in float roughness ) {
	const float LUT_SIZE = 64.0;
	const float LUT_SCALE = ( LUT_SIZE - 1.0 ) / LUT_SIZE;
	const float LUT_BIAS = 0.5 / LUT_SIZE;
	float dotNV = saturate( dot( N, V ) );
	vec2 uv = vec2( roughness, sqrt( 1.0 - dotNV ) );
	uv = uv * LUT_SCALE + LUT_BIAS;
	return uv;
}
float LTC_ClippedSphereFormFactor( const in vec3 f ) {
	float l = length( f );
	return max( ( l * l + f.z ) / ( l + 1.0 ), 0.0 );
}
vec3 LTC_EdgeVectorFormFactor( const in vec3 v1, const in vec3 v2 ) {
	float x = dot( v1, v2 );
	float y = abs( x );
	float a = 0.8543985 + ( 0.4965155 + 0.0145206 * y ) * y;
	float b = 3.4175940 + ( 4.1616724 + y ) * y;
	float v = a / b;
	float theta_sintheta = ( x > 0.0 ) ? v : 0.5 * inversesqrt( max( 1.0 - x * x, 1e-7 ) ) - v;
	return cross( v1, v2 ) * theta_sintheta;
}
vec3 LTC_Evaluate( const in vec3 N, const in vec3 V, const in vec3 P, const in mat3 mInv, const in vec3 rectCoords[ 4 ] ) {
	vec3 v1 = rectCoords[ 1 ] - rectCoords[ 0 ];
	vec3 v2 = rectCoords[ 3 ] - rectCoords[ 0 ];
	vec3 lightNormal = cross( v1, v2 );
	if( dot( lightNormal, P - rectCoords[ 0 ] ) < 0.0 ) return vec3( 0.0 );
	vec3 T1, T2;
	T1 = normalize( V - N * dot( V, N ) );
	T2 = - cross( N, T1 );
	mat3 mat = mInv * transposeMat3( mat3( T1, T2, N ) );
	vec3 coords[ 4 ];
	coords[ 0 ] = mat * ( rectCoords[ 0 ] - P );
	coords[ 1 ] = mat * ( rectCoords[ 1 ] - P );
	coords[ 2 ] = mat * ( rectCoords[ 2 ] - P );
	coords[ 3 ] = mat * ( rectCoords[ 3 ] - P );
	coords[ 0 ] = normalize( coords[ 0 ] );
	coords[ 1 ] = normalize( coords[ 1 ] );
	coords[ 2 ] = normalize( coords[ 2 ] );
	coords[ 3 ] = normalize( coords[ 3 ] );
	vec3 vectorFormFactor = vec3( 0.0 );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 0 ], coords[ 1 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 1 ], coords[ 2 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 2 ], coords[ 3 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 3 ], coords[ 0 ] );
	float result = LTC_ClippedSphereFormFactor( vectorFormFactor );
	return vec3( result );
}
#if defined( USE_SHEEN )
float D_Charlie( float roughness, float dotNH ) {
	float alpha = pow2( roughness );
	float invAlpha = 1.0 / alpha;
	float cos2h = dotNH * dotNH;
	float sin2h = max( 1.0 - cos2h, 0.0078125 );
	return ( 2.0 + invAlpha ) * pow( sin2h, invAlpha * 0.5 ) / ( 2.0 * PI );
}
float V_Neubelt( float dotNV, float dotNL ) {
	return saturate( 1.0 / ( 4.0 * ( dotNL + dotNV - dotNL * dotNV ) ) );
}
vec3 BRDF_Sheen( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, vec3 sheenColor, const in float sheenRoughness ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float D = D_Charlie( sheenRoughness, dotNH );
	float V = V_Neubelt( dotNV, dotNL );
	return sheenColor * ( D * V );
}
#endif
float IBLSheenBRDF( const in vec3 normal, const in vec3 viewDir, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	float r2 = roughness * roughness;
	float a = roughness < 0.25 ? -339.2 * r2 + 161.4 * roughness - 25.9 : -8.48 * r2 + 14.3 * roughness - 9.95;
	float b = roughness < 0.25 ? 44.0 * r2 - 23.7 * roughness + 3.26 : 1.97 * r2 - 3.27 * roughness + 0.72;
	float DG = exp( a * dotNV + b ) + ( roughness < 0.25 ? 0.0 : 0.1 * ( roughness - 0.25 ) );
	return saturate( DG * RECIPROCAL_PI );
}
vec2 DFGApprox( const in vec3 normal, const in vec3 viewDir, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	const vec4 c0 = vec4( - 1, - 0.0275, - 0.572, 0.022 );
	const vec4 c1 = vec4( 1, 0.0425, 1.04, - 0.04 );
	vec4 r = roughness * c0 + c1;
	float a004 = min( r.x * r.x, exp2( - 9.28 * dotNV ) ) * r.x + r.y;
	vec2 fab = vec2( - 1.04, 1.04 ) * a004 + r.zw;
	return fab;
}
vec3 EnvironmentBRDF( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness ) {
	vec2 fab = DFGApprox( normal, viewDir, roughness );
	return specularColor * fab.x + specularF90 * fab.y;
}
#ifdef USE_IRIDESCENCE
void computeMultiscatteringIridescence( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float iridescence, const in vec3 iridescenceF0, const in float roughness, inout vec3 singleScatter, inout vec3 multiScatter ) {
#else
void computeMultiscattering( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness, inout vec3 singleScatter, inout vec3 multiScatter ) {
#endif
	vec2 fab = DFGApprox( normal, viewDir, roughness );
	#ifdef USE_IRIDESCENCE
		vec3 Fr = mix( specularColor, iridescenceF0, iridescence );
	#else
		vec3 Fr = specularColor;
	#endif
	vec3 FssEss = Fr * fab.x + specularF90 * fab.y;
	float Ess = fab.x + fab.y;
	float Ems = 1.0 - Ess;
	vec3 Favg = Fr + ( 1.0 - Fr ) * 0.047619;	vec3 Fms = FssEss * Favg / ( 1.0 - Ems * Favg );
	singleScatter += FssEss;
	multiScatter += Fms * Ems;
}
#if NUM_RECT_AREA_LIGHTS > 0
	void RE_Direct_RectArea_Physical( const in RectAreaLight rectAreaLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
		vec3 normal = geometryNormal;
		vec3 viewDir = geometryViewDir;
		vec3 position = geometryPosition;
		vec3 lightPos = rectAreaLight.position;
		vec3 halfWidth = rectAreaLight.halfWidth;
		vec3 halfHeight = rectAreaLight.halfHeight;
		vec3 lightColor = rectAreaLight.color;
		float roughness = material.roughness;
		vec3 rectCoords[ 4 ];
		rectCoords[ 0 ] = lightPos + halfWidth - halfHeight;		rectCoords[ 1 ] = lightPos - halfWidth - halfHeight;
		rectCoords[ 2 ] = lightPos - halfWidth + halfHeight;
		rectCoords[ 3 ] = lightPos + halfWidth + halfHeight;
		vec2 uv = LTC_Uv( normal, viewDir, roughness );
		vec4 t1 = texture2D( ltc_1, uv );
		vec4 t2 = texture2D( ltc_2, uv );
		mat3 mInv = mat3(
			vec3( t1.x, 0, t1.y ),
			vec3(    0, 1,    0 ),
			vec3( t1.z, 0, t1.w )
		);
		vec3 fresnel = ( material.specularColor * t2.x + ( vec3( 1.0 ) - material.specularColor ) * t2.y );
		reflectedLight.directSpecular += lightColor * fresnel * LTC_Evaluate( normal, viewDir, position, mInv, rectCoords );
		reflectedLight.directDiffuse += lightColor * material.diffuseColor * LTC_Evaluate( normal, viewDir, position, mat3( 1.0 ), rectCoords );
	}
#endif
void RE_Direct_Physical( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	#ifdef USE_CLEARCOAT
		float dotNLcc = saturate( dot( geometryClearcoatNormal, directLight.direction ) );
		vec3 ccIrradiance = dotNLcc * directLight.color;
		clearcoatSpecularDirect += ccIrradiance * BRDF_GGX_Clearcoat( directLight.direction, geometryViewDir, geometryClearcoatNormal, material );
	#endif
	#ifdef USE_SHEEN
		sheenSpecularDirect += irradiance * BRDF_Sheen( directLight.direction, geometryViewDir, geometryNormal, material.sheenColor, material.sheenRoughness );
	#endif
	reflectedLight.directSpecular += irradiance * BRDF_GGX( directLight.direction, geometryViewDir, geometryNormal, material );
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Physical( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectSpecular_Physical( const in vec3 radiance, const in vec3 irradiance, const in vec3 clearcoatRadiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight) {
	#ifdef USE_CLEARCOAT
		clearcoatSpecularIndirect += clearcoatRadiance * EnvironmentBRDF( geometryClearcoatNormal, geometryViewDir, material.clearcoatF0, material.clearcoatF90, material.clearcoatRoughness );
	#endif
	#ifdef USE_SHEEN
		sheenSpecularIndirect += irradiance * material.sheenColor * IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
	#endif
	vec3 singleScattering = vec3( 0.0 );
	vec3 multiScattering = vec3( 0.0 );
	vec3 cosineWeightedIrradiance = irradiance * RECIPROCAL_PI;
	#ifdef USE_IRIDESCENCE
		computeMultiscatteringIridescence( geometryNormal, geometryViewDir, material.specularColor, material.specularF90, material.iridescence, material.iridescenceFresnel, material.roughness, singleScattering, multiScattering );
	#else
		computeMultiscattering( geometryNormal, geometryViewDir, material.specularColor, material.specularF90, material.roughness, singleScattering, multiScattering );
	#endif
	vec3 totalScattering = singleScattering + multiScattering;
	vec3 diffuse = material.diffuseColor * ( 1.0 - max( max( totalScattering.r, totalScattering.g ), totalScattering.b ) );
	reflectedLight.indirectSpecular += radiance * singleScattering;
	reflectedLight.indirectSpecular += multiScattering * cosineWeightedIrradiance;
	reflectedLight.indirectDiffuse += diffuse * cosineWeightedIrradiance;
}
#define RE_Direct				RE_Direct_Physical
#define RE_Direct_RectArea		RE_Direct_RectArea_Physical
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Physical
#define RE_IndirectSpecular		RE_IndirectSpecular_Physical
float computeSpecularOcclusion( const in float dotNV, const in float ambientOcclusion, const in float roughness ) {
	return saturate( pow( dotNV + ambientOcclusion, exp2( - 16.0 * roughness - 1.0 ) ) - 1.0 + ambientOcclusion );
}`,jE=`
vec3 geometryPosition = - vViewPosition;
vec3 geometryNormal = normal;
vec3 geometryViewDir = ( isOrthographic ) ? vec3( 0, 0, 1 ) : normalize( vViewPosition );
vec3 geometryClearcoatNormal = vec3( 0.0 );
#ifdef USE_CLEARCOAT
	geometryClearcoatNormal = clearcoatNormal;
#endif
#ifdef USE_IRIDESCENCE
	float dotNVi = saturate( dot( normal, geometryViewDir ) );
	if ( material.iridescenceThickness == 0.0 ) {
		material.iridescence = 0.0;
	} else {
		material.iridescence = saturate( material.iridescence );
	}
	if ( material.iridescence > 0.0 ) {
		material.iridescenceFresnel = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.specularColor );
		material.iridescenceF0 = Schlick_to_F0( material.iridescenceFresnel, 1.0, dotNVi );
	}
#endif
IncidentLight directLight;
#if ( NUM_POINT_LIGHTS > 0 ) && defined( RE_Direct )
	PointLight pointLight;
	#if defined( USE_SHADOWMAP ) && NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHTS; i ++ ) {
		pointLight = pointLights[ i ];
		getPointLightInfo( pointLight, geometryPosition, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_POINT_LIGHT_SHADOWS )
		pointLightShadow = pointLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getPointShadow( pointShadowMap[ i ], pointLightShadow.shadowMapSize, pointLightShadow.shadowIntensity, pointLightShadow.shadowBias, pointLightShadow.shadowRadius, vPointShadowCoord[ i ], pointLightShadow.shadowCameraNear, pointLightShadow.shadowCameraFar ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_SPOT_LIGHTS > 0 ) && defined( RE_Direct )
	SpotLight spotLight;
	vec4 spotColor;
	vec3 spotLightCoord;
	bool inSpotLightMap;
	#if defined( USE_SHADOWMAP ) && NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHTS; i ++ ) {
		spotLight = spotLights[ i ];
		getSpotLightInfo( spotLight, geometryPosition, directLight );
		#if ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#define SPOT_LIGHT_MAP_INDEX UNROLLED_LOOP_INDEX
		#elif ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		#define SPOT_LIGHT_MAP_INDEX NUM_SPOT_LIGHT_MAPS
		#else
		#define SPOT_LIGHT_MAP_INDEX ( UNROLLED_LOOP_INDEX - NUM_SPOT_LIGHT_SHADOWS + NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#endif
		#if ( SPOT_LIGHT_MAP_INDEX < NUM_SPOT_LIGHT_MAPS )
			spotLightCoord = vSpotLightCoord[ i ].xyz / vSpotLightCoord[ i ].w;
			inSpotLightMap = all( lessThan( abs( spotLightCoord * 2. - 1. ), vec3( 1.0 ) ) );
			spotColor = texture2D( spotLightMap[ SPOT_LIGHT_MAP_INDEX ], spotLightCoord.xy );
			directLight.color = inSpotLightMap ? directLight.color * spotColor.rgb : directLight.color;
		#endif
		#undef SPOT_LIGHT_MAP_INDEX
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		spotLightShadow = spotLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( spotShadowMap[ i ], spotLightShadow.shadowMapSize, spotLightShadow.shadowIntensity, spotLightShadow.shadowBias, spotLightShadow.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_DIR_LIGHTS > 0 ) && defined( RE_Direct )
	DirectionalLight directionalLight;
	#if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHTS; i ++ ) {
		directionalLight = directionalLights[ i ];
		getDirectionalLightInfo( directionalLight, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_DIR_LIGHT_SHADOWS )
		directionalLightShadow = directionalLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( directionalShadowMap[ i ], directionalLightShadow.shadowMapSize, directionalLightShadow.shadowIntensity, directionalLightShadow.shadowBias, directionalLightShadow.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_RECT_AREA_LIGHTS > 0 ) && defined( RE_Direct_RectArea )
	RectAreaLight rectAreaLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_RECT_AREA_LIGHTS; i ++ ) {
		rectAreaLight = rectAreaLights[ i ];
		RE_Direct_RectArea( rectAreaLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if defined( RE_IndirectDiffuse )
	vec3 iblIrradiance = vec3( 0.0 );
	vec3 irradiance = getAmbientLightIrradiance( ambientLightColor );
	#if defined( USE_LIGHT_PROBES )
		irradiance += getLightProbeIrradiance( lightProbe, geometryNormal );
	#endif
	#if ( NUM_HEMI_LIGHTS > 0 )
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_HEMI_LIGHTS; i ++ ) {
			irradiance += getHemisphereLightIrradiance( hemisphereLights[ i ], geometryNormal );
		}
		#pragma unroll_loop_end
	#endif
#endif
#if defined( RE_IndirectSpecular )
	vec3 radiance = vec3( 0.0 );
	vec3 clearcoatRadiance = vec3( 0.0 );
#endif`,WE=`#if defined( RE_IndirectDiffuse )
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		vec3 lightMapIrradiance = lightMapTexel.rgb * lightMapIntensity;
		irradiance += lightMapIrradiance;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD ) && defined( ENVMAP_TYPE_CUBE_UV )
		iblIrradiance += getIBLIrradiance( geometryNormal );
	#endif
#endif
#if defined( USE_ENVMAP ) && defined( RE_IndirectSpecular )
	#ifdef USE_ANISOTROPY
		radiance += getIBLAnisotropyRadiance( geometryViewDir, geometryNormal, material.roughness, material.anisotropyB, material.anisotropy );
	#else
		radiance += getIBLRadiance( geometryViewDir, geometryNormal, material.roughness );
	#endif
	#ifdef USE_CLEARCOAT
		clearcoatRadiance += getIBLRadiance( geometryViewDir, geometryClearcoatNormal, material.clearcoatRoughness );
	#endif
#endif`,XE=`#if defined( RE_IndirectDiffuse )
	RE_IndirectDiffuse( irradiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif`,$E=`#if defined( USE_LOGDEPTHBUF )
	gl_FragDepth = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`,YE=`#if defined( USE_LOGDEPTHBUF )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,qE=`#ifdef USE_LOGDEPTHBUF
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,KE=`#ifdef USE_LOGDEPTHBUF
	vFragDepth = 1.0 + gl_Position.w;
	vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
#endif`,ZE=`#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vMapUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`,JE=`#ifdef USE_MAP
	uniform sampler2D map;
#endif`,QE=`#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
	#if defined( USE_POINTS_UV )
		vec2 uv = vUv;
	#else
		vec2 uv = ( uvTransform * vec3( gl_PointCoord.x, 1.0 - gl_PointCoord.y, 1 ) ).xy;
	#endif
#endif
#ifdef USE_MAP
	diffuseColor *= texture2D( map, uv );
#endif
#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, uv ).g;
#endif`,ew=`#if defined( USE_POINTS_UV )
	varying vec2 vUv;
#else
	#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
		uniform mat3 uvTransform;
	#endif
#endif
#ifdef USE_MAP
	uniform sampler2D map;
#endif
#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,tw=`float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vMetalnessMapUv );
	metalnessFactor *= texelMetalness.b;
#endif`,nw=`#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`,iw=`#ifdef USE_INSTANCING_MORPH
	float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	float morphTargetBaseInfluence = texelFetch( morphTexture, ivec2( 0, gl_InstanceID ), 0 ).r;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		morphTargetInfluences[i] =  texelFetch( morphTexture, ivec2( i + 1, gl_InstanceID ), 0 ).r;
	}
#endif`,rw=`#if defined( USE_MORPHCOLORS )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`,sw=`#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,ow=`#ifdef USE_MORPHTARGETS
	#ifndef USE_INSTANCING_MORPH
		uniform float morphTargetBaseInfluence;
		uniform float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	#endif
	uniform sampler2DArray morphTargetsTexture;
	uniform ivec2 morphTargetsTextureSize;
	vec4 getMorph( const in int vertexIndex, const in int morphTargetIndex, const in int offset ) {
		int texelIndex = vertexIndex * MORPHTARGETS_TEXTURE_STRIDE + offset;
		int y = texelIndex / morphTargetsTextureSize.x;
		int x = texelIndex - y * morphTargetsTextureSize.x;
		ivec3 morphUV = ivec3( x, y, morphTargetIndex );
		return texelFetch( morphTargetsTexture, morphUV, 0 );
	}
#endif`,aw=`#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,lw=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
#ifdef FLAT_SHADED
	vec3 fdx = dFdx( vViewPosition );
	vec3 fdy = dFdy( vViewPosition );
	vec3 normal = normalize( cross( fdx, fdy ) );
#else
	vec3 normal = normalize( vNormal );
	#ifdef DOUBLE_SIDED
		normal *= faceDirection;
	#endif
#endif
#if defined( USE_NORMALMAP_TANGENTSPACE ) || defined( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY )
	#ifdef USE_TANGENT
		mat3 tbn = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn = getTangentFrame( - vViewPosition, normal,
		#if defined( USE_NORMALMAP )
			vNormalMapUv
		#elif defined( USE_CLEARCOAT_NORMALMAP )
			vClearcoatNormalMapUv
		#else
			vUv
		#endif
		);
	#endif
	#if defined( DOUBLE_SIDED ) && ! defined( FLAT_SHADED )
		tbn[0] *= faceDirection;
		tbn[1] *= faceDirection;
	#endif
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	#ifdef USE_TANGENT
		mat3 tbn2 = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn2 = getTangentFrame( - vViewPosition, normal, vClearcoatNormalMapUv );
	#endif
	#if defined( DOUBLE_SIDED ) && ! defined( FLAT_SHADED )
		tbn2[0] *= faceDirection;
		tbn2[1] *= faceDirection;
	#endif
#endif
vec3 nonPerturbedNormal = normal;`,cw=`#ifdef USE_NORMALMAP_OBJECTSPACE
	normal = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#ifdef FLIP_SIDED
		normal = - normal;
	#endif
	#ifdef DOUBLE_SIDED
		normal = normal * faceDirection;
	#endif
	normal = normalize( normalMatrix * normal );
#elif defined( USE_NORMALMAP_TANGENTSPACE )
	vec3 mapN = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	mapN.xy *= normalScale;
	normal = normalize( tbn * mapN );
#elif defined( USE_BUMPMAP )
	normal = perturbNormalArb( - vViewPosition, normal, dHdxy_fwd(), faceDirection );
#endif`,uw=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,dw=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,hw=`#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
	#endif
#endif`,fw=`#ifdef USE_NORMALMAP
	uniform sampler2D normalMap;
	uniform vec2 normalScale;
#endif
#ifdef USE_NORMALMAP_OBJECTSPACE
	uniform mat3 normalMatrix;
#endif
#if ! defined ( USE_TANGENT ) && ( defined ( USE_NORMALMAP_TANGENTSPACE ) || defined ( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY ) )
	mat3 getTangentFrame( vec3 eye_pos, vec3 surf_norm, vec2 uv ) {
		vec3 q0 = dFdx( eye_pos.xyz );
		vec3 q1 = dFdy( eye_pos.xyz );
		vec2 st0 = dFdx( uv.st );
		vec2 st1 = dFdy( uv.st );
		vec3 N = surf_norm;
		vec3 q1perp = cross( q1, N );
		vec3 q0perp = cross( N, q0 );
		vec3 T = q1perp * st0.x + q0perp * st1.x;
		vec3 B = q1perp * st0.y + q0perp * st1.y;
		float det = max( dot( T, T ), dot( B, B ) );
		float scale = ( det == 0.0 ) ? 0.0 : inversesqrt( det );
		return mat3( T * scale, B * scale, N );
	}
#endif`,pw=`#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = nonPerturbedNormal;
#endif`,mw=`#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vClearcoatNormalMapUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	clearcoatNormal = normalize( tbn2 * clearcoatMapN );
#endif`,gw=`#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif`,_w=`#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`,vw=`#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= material.transmissionAlpha;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,xw=`vec3 packNormalToRGB( const in vec3 normal ) {
	return normalize( normal ) * 0.5 + 0.5;
}
vec3 unpackRGBToNormal( const in vec3 rgb ) {
	return 2.0 * rgb.xyz - 1.0;
}
const float PackUpscale = 256. / 255.;const float UnpackDownscale = 255. / 256.;const float ShiftRight8 = 1. / 256.;
const float Inv255 = 1. / 255.;
const vec4 PackFactors = vec4( 1.0, 256.0, 256.0 * 256.0, 256.0 * 256.0 * 256.0 );
const vec2 UnpackFactors2 = vec2( UnpackDownscale, 1.0 / PackFactors.g );
const vec3 UnpackFactors3 = vec3( UnpackDownscale / PackFactors.rg, 1.0 / PackFactors.b );
const vec4 UnpackFactors4 = vec4( UnpackDownscale / PackFactors.rgb, 1.0 / PackFactors.a );
vec4 packDepthToRGBA( const in float v ) {
	if( v <= 0.0 )
		return vec4( 0., 0., 0., 0. );
	if( v >= 1.0 )
		return vec4( 1., 1., 1., 1. );
	float vuf;
	float af = modf( v * PackFactors.a, vuf );
	float bf = modf( vuf * ShiftRight8, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec4( vuf * Inv255, gf * PackUpscale, bf * PackUpscale, af );
}
vec3 packDepthToRGB( const in float v ) {
	if( v <= 0.0 )
		return vec3( 0., 0., 0. );
	if( v >= 1.0 )
		return vec3( 1., 1., 1. );
	float vuf;
	float bf = modf( v * PackFactors.b, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec3( vuf * Inv255, gf * PackUpscale, bf );
}
vec2 packDepthToRG( const in float v ) {
	if( v <= 0.0 )
		return vec2( 0., 0. );
	if( v >= 1.0 )
		return vec2( 1., 1. );
	float vuf;
	float gf = modf( v * 256., vuf );
	return vec2( vuf * Inv255, gf );
}
float unpackRGBAToDepth( const in vec4 v ) {
	return dot( v, UnpackFactors4 );
}
float unpackRGBToDepth( const in vec3 v ) {
	return dot( v, UnpackFactors3 );
}
float unpackRGToDepth( const in vec2 v ) {
	return v.r * UnpackFactors2.r + v.g * UnpackFactors2.g;
}
vec4 pack2HalfToRGBA( const in vec2 v ) {
	vec4 r = vec4( v.x, fract( v.x * 255.0 ), v.y, fract( v.y * 255.0 ) );
	return vec4( r.x - r.y / 255.0, r.y, r.z - r.w / 255.0, r.w );
}
vec2 unpackRGBATo2Half( const in vec4 v ) {
	return vec2( v.x + ( v.y / 255.0 ), v.z + ( v.w / 255.0 ) );
}
float viewZToOrthographicDepth( const in float viewZ, const in float near, const in float far ) {
	return ( viewZ + near ) / ( near - far );
}
float orthographicDepthToViewZ( const in float depth, const in float near, const in float far ) {
	return depth * ( near - far ) - near;
}
float viewZToPerspectiveDepth( const in float viewZ, const in float near, const in float far ) {
	return ( ( near + viewZ ) * far ) / ( ( far - near ) * viewZ );
}
float perspectiveDepthToViewZ( const in float depth, const in float near, const in float far ) {
	return ( near * far ) / ( ( far - near ) * depth - far );
}`,yw=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,Sw=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,Mw=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,Ew=`#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`,ww=`float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vRoughnessMapUv );
	roughnessFactor *= texelRoughness.g;
#endif`,Tw=`#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`,Aw=`#if NUM_SPOT_LIGHT_COORDS > 0
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#if NUM_SPOT_LIGHT_MAPS > 0
	uniform sampler2D spotLightMap[ NUM_SPOT_LIGHT_MAPS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform sampler2D directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		uniform sampler2D spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform sampler2D pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
	float texture2DCompare( sampler2D depths, vec2 uv, float compare ) {
		return step( compare, unpackRGBAToDepth( texture2D( depths, uv ) ) );
	}
	vec2 texture2DDistribution( sampler2D shadow, vec2 uv ) {
		return unpackRGBATo2Half( texture2D( shadow, uv ) );
	}
	float VSMShadow (sampler2D shadow, vec2 uv, float compare ){
		float occlusion = 1.0;
		vec2 distribution = texture2DDistribution( shadow, uv );
		float hard_shadow = step( compare , distribution.x );
		if (hard_shadow != 1.0 ) {
			float distance = compare - distribution.x ;
			float variance = max( 0.00000, distribution.y * distribution.y );
			float softness_probability = variance / (variance + distance * distance );			softness_probability = clamp( ( softness_probability - 0.3 ) / ( 0.95 - 0.3 ), 0.0, 1.0 );			occlusion = clamp( max( hard_shadow, softness_probability ), 0.0, 1.0 );
		}
		return occlusion;
	}
	float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
		float shadow = 1.0;
		shadowCoord.xyz /= shadowCoord.w;
		shadowCoord.z += shadowBias;
		bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
		bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
		if ( frustumTest ) {
		#if defined( SHADOWMAP_TYPE_PCF )
			vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
			float dx0 = - texelSize.x * shadowRadius;
			float dy0 = - texelSize.y * shadowRadius;
			float dx1 = + texelSize.x * shadowRadius;
			float dy1 = + texelSize.y * shadowRadius;
			float dx2 = dx0 / 2.0;
			float dy2 = dy0 / 2.0;
			float dx3 = dx1 / 2.0;
			float dy3 = dy1 / 2.0;
			shadow = (
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, dy0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, dy0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx2, dy2 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy2 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx3, dy2 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx2, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy, shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx3, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx2, dy3 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy3 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx3, dy3 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, dy1 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy1 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, dy1 ), shadowCoord.z )
			) * ( 1.0 / 17.0 );
		#elif defined( SHADOWMAP_TYPE_PCF_SOFT )
			vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
			float dx = texelSize.x;
			float dy = texelSize.y;
			vec2 uv = shadowCoord.xy;
			vec2 f = fract( uv * shadowMapSize + 0.5 );
			uv -= f * texelSize;
			shadow = (
				texture2DCompare( shadowMap, uv, shadowCoord.z ) +
				texture2DCompare( shadowMap, uv + vec2( dx, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, uv + vec2( 0.0, dy ), shadowCoord.z ) +
				texture2DCompare( shadowMap, uv + texelSize, shadowCoord.z ) +
				mix( texture2DCompare( shadowMap, uv + vec2( -dx, 0.0 ), shadowCoord.z ),
					 texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, 0.0 ), shadowCoord.z ),
					 f.x ) +
				mix( texture2DCompare( shadowMap, uv + vec2( -dx, dy ), shadowCoord.z ),
					 texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, dy ), shadowCoord.z ),
					 f.x ) +
				mix( texture2DCompare( shadowMap, uv + vec2( 0.0, -dy ), shadowCoord.z ),
					 texture2DCompare( shadowMap, uv + vec2( 0.0, 2.0 * dy ), shadowCoord.z ),
					 f.y ) +
				mix( texture2DCompare( shadowMap, uv + vec2( dx, -dy ), shadowCoord.z ),
					 texture2DCompare( shadowMap, uv + vec2( dx, 2.0 * dy ), shadowCoord.z ),
					 f.y ) +
				mix( mix( texture2DCompare( shadowMap, uv + vec2( -dx, -dy ), shadowCoord.z ),
						  texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, -dy ), shadowCoord.z ),
						  f.x ),
					 mix( texture2DCompare( shadowMap, uv + vec2( -dx, 2.0 * dy ), shadowCoord.z ),
						  texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, 2.0 * dy ), shadowCoord.z ),
						  f.x ),
					 f.y )
			) * ( 1.0 / 9.0 );
		#elif defined( SHADOWMAP_TYPE_VSM )
			shadow = VSMShadow( shadowMap, shadowCoord.xy, shadowCoord.z );
		#else
			shadow = texture2DCompare( shadowMap, shadowCoord.xy, shadowCoord.z );
		#endif
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	vec2 cubeToUV( vec3 v, float texelSizeY ) {
		vec3 absV = abs( v );
		float scaleToCube = 1.0 / max( absV.x, max( absV.y, absV.z ) );
		absV *= scaleToCube;
		v *= scaleToCube * ( 1.0 - 2.0 * texelSizeY );
		vec2 planar = v.xy;
		float almostATexel = 1.5 * texelSizeY;
		float almostOne = 1.0 - almostATexel;
		if ( absV.z >= almostOne ) {
			if ( v.z > 0.0 )
				planar.x = 4.0 - v.x;
		} else if ( absV.x >= almostOne ) {
			float signX = sign( v.x );
			planar.x = v.z * signX + 2.0 * signX;
		} else if ( absV.y >= almostOne ) {
			float signY = sign( v.y );
			planar.x = v.x + 2.0 * signY + 2.0;
			planar.y = v.z * signY - 2.0;
		}
		return vec2( 0.125, 0.25 ) * planar + vec2( 0.375, 0.75 );
	}
	float getPointShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		
		float lightToPositionLength = length( lightToPosition );
		if ( lightToPositionLength - shadowCameraFar <= 0.0 && lightToPositionLength - shadowCameraNear >= 0.0 ) {
			float dp = ( lightToPositionLength - shadowCameraNear ) / ( shadowCameraFar - shadowCameraNear );			dp += shadowBias;
			vec3 bd3D = normalize( lightToPosition );
			vec2 texelSize = vec2( 1.0 ) / ( shadowMapSize * vec2( 4.0, 2.0 ) );
			#if defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_PCF_SOFT ) || defined( SHADOWMAP_TYPE_VSM )
				vec2 offset = vec2( - 1, 1 ) * shadowRadius * texelSize.y;
				shadow = (
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xyy, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yyy, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xyx, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yyx, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xxy, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yxy, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xxx, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yxx, texelSize.y ), dp )
				) * ( 1.0 / 9.0 );
			#else
				shadow = texture2DCompare( shadowMap, cubeToUV( bd3D, texelSize.y ), dp );
			#endif
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
#endif`,Cw=`#if NUM_SPOT_LIGHT_COORDS > 0
	uniform mat4 spotLightMatrix[ NUM_SPOT_LIGHT_COORDS ];
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform mat4 directionalShadowMatrix[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform mat4 pointShadowMatrix[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
#endif`,bw=`#if ( defined( USE_SHADOWMAP ) && ( NUM_DIR_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0 ) ) || ( NUM_SPOT_LIGHT_COORDS > 0 )
	vec3 shadowWorldNormal = inverseTransformDirection( transformedNormal, viewMatrix );
	vec4 shadowWorldPosition;
#endif
#if defined( USE_SHADOWMAP )
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * directionalLightShadows[ i ].shadowNormalBias, 0 );
			vDirectionalShadowCoord[ i ] = directionalShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * pointLightShadows[ i ].shadowNormalBias, 0 );
			vPointShadowCoord[ i ] = pointShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
#endif
#if NUM_SPOT_LIGHT_COORDS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_COORDS; i ++ ) {
		shadowWorldPosition = worldPosition;
		#if ( defined( USE_SHADOWMAP ) && UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
			shadowWorldPosition.xyz += shadowWorldNormal * spotLightShadows[ i ].shadowNormalBias;
		#endif
		vSpotLightCoord[ i ] = spotLightMatrix[ i ] * shadowWorldPosition;
	}
	#pragma unroll_loop_end
#endif`,Rw=`float getShadowMask() {
	float shadow = 1.0;
	#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
		directionalLight = directionalLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( directionalShadowMap[ i ], directionalLight.shadowMapSize, directionalLight.shadowIntensity, directionalLight.shadowBias, directionalLight.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_SHADOWS; i ++ ) {
		spotLight = spotLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( spotShadowMap[ i ], spotLight.shadowMapSize, spotLight.shadowIntensity, spotLight.shadowBias, spotLight.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
		pointLight = pointLightShadows[ i ];
		shadow *= receiveShadow ? getPointShadow( pointShadowMap[ i ], pointLight.shadowMapSize, pointLight.shadowIntensity, pointLight.shadowBias, pointLight.shadowRadius, vPointShadowCoord[ i ], pointLight.shadowCameraNear, pointLight.shadowCameraFar ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#endif
	return shadow;
}`,Pw=`#ifdef USE_SKINNING
	mat4 boneMatX = getBoneMatrix( skinIndex.x );
	mat4 boneMatY = getBoneMatrix( skinIndex.y );
	mat4 boneMatZ = getBoneMatrix( skinIndex.z );
	mat4 boneMatW = getBoneMatrix( skinIndex.w );
#endif`,Lw=`#ifdef USE_SKINNING
	uniform mat4 bindMatrix;
	uniform mat4 bindMatrixInverse;
	uniform highp sampler2D boneTexture;
	mat4 getBoneMatrix( const in float i ) {
		int size = textureSize( boneTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( boneTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( boneTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( boneTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( boneTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
#endif`,Nw=`#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`,Dw=`#ifdef USE_SKINNING
	mat4 skinMatrix = mat4( 0.0 );
	skinMatrix += skinWeight.x * boneMatX;
	skinMatrix += skinWeight.y * boneMatY;
	skinMatrix += skinWeight.z * boneMatZ;
	skinMatrix += skinWeight.w * boneMatW;
	skinMatrix = bindMatrixInverse * skinMatrix * bindMatrix;
	objectNormal = vec4( skinMatrix * vec4( objectNormal, 0.0 ) ).xyz;
	#ifdef USE_TANGENT
		objectTangent = vec4( skinMatrix * vec4( objectTangent, 0.0 ) ).xyz;
	#endif
#endif`,Iw=`float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vSpecularMapUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`,Uw=`#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`,Ow=`#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`,Fw=`#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
uniform float toneMappingExposure;
vec3 LinearToneMapping( vec3 color ) {
	return saturate( toneMappingExposure * color );
}
vec3 ReinhardToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	return saturate( color / ( vec3( 1.0 ) + color ) );
}
vec3 CineonToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	color = max( vec3( 0.0 ), color - 0.004 );
	return pow( ( color * ( 6.2 * color + 0.5 ) ) / ( color * ( 6.2 * color + 1.7 ) + 0.06 ), vec3( 2.2 ) );
}
vec3 RRTAndODTFit( vec3 v ) {
	vec3 a = v * ( v + 0.0245786 ) - 0.000090537;
	vec3 b = v * ( 0.983729 * v + 0.4329510 ) + 0.238081;
	return a / b;
}
vec3 ACESFilmicToneMapping( vec3 color ) {
	const mat3 ACESInputMat = mat3(
		vec3( 0.59719, 0.07600, 0.02840 ),		vec3( 0.35458, 0.90834, 0.13383 ),
		vec3( 0.04823, 0.01566, 0.83777 )
	);
	const mat3 ACESOutputMat = mat3(
		vec3(  1.60475, -0.10208, -0.00327 ),		vec3( -0.53108,  1.10813, -0.07276 ),
		vec3( -0.07367, -0.00605,  1.07602 )
	);
	color *= toneMappingExposure / 0.6;
	color = ACESInputMat * color;
	color = RRTAndODTFit( color );
	color = ACESOutputMat * color;
	return saturate( color );
}
const mat3 LINEAR_REC2020_TO_LINEAR_SRGB = mat3(
	vec3( 1.6605, - 0.1246, - 0.0182 ),
	vec3( - 0.5876, 1.1329, - 0.1006 ),
	vec3( - 0.0728, - 0.0083, 1.1187 )
);
const mat3 LINEAR_SRGB_TO_LINEAR_REC2020 = mat3(
	vec3( 0.6274, 0.0691, 0.0164 ),
	vec3( 0.3293, 0.9195, 0.0880 ),
	vec3( 0.0433, 0.0113, 0.8956 )
);
vec3 agxDefaultContrastApprox( vec3 x ) {
	vec3 x2 = x * x;
	vec3 x4 = x2 * x2;
	return + 15.5 * x4 * x2
		- 40.14 * x4 * x
		+ 31.96 * x4
		- 6.868 * x2 * x
		+ 0.4298 * x2
		+ 0.1191 * x
		- 0.00232;
}
vec3 AgXToneMapping( vec3 color ) {
	const mat3 AgXInsetMatrix = mat3(
		vec3( 0.856627153315983, 0.137318972929847, 0.11189821299995 ),
		vec3( 0.0951212405381588, 0.761241990602591, 0.0767994186031903 ),
		vec3( 0.0482516061458583, 0.101439036467562, 0.811302368396859 )
	);
	const mat3 AgXOutsetMatrix = mat3(
		vec3( 1.1271005818144368, - 0.1413297634984383, - 0.14132976349843826 ),
		vec3( - 0.11060664309660323, 1.157823702216272, - 0.11060664309660294 ),
		vec3( - 0.016493938717834573, - 0.016493938717834257, 1.2519364065950405 )
	);
	const float AgxMinEv = - 12.47393;	const float AgxMaxEv = 4.026069;
	color *= toneMappingExposure;
	color = LINEAR_SRGB_TO_LINEAR_REC2020 * color;
	color = AgXInsetMatrix * color;
	color = max( color, 1e-10 );	color = log2( color );
	color = ( color - AgxMinEv ) / ( AgxMaxEv - AgxMinEv );
	color = clamp( color, 0.0, 1.0 );
	color = agxDefaultContrastApprox( color );
	color = AgXOutsetMatrix * color;
	color = pow( max( vec3( 0.0 ), color ), vec3( 2.2 ) );
	color = LINEAR_REC2020_TO_LINEAR_SRGB * color;
	color = clamp( color, 0.0, 1.0 );
	return color;
}
vec3 NeutralToneMapping( vec3 color ) {
	const float StartCompression = 0.8 - 0.04;
	const float Desaturation = 0.15;
	color *= toneMappingExposure;
	float x = min( color.r, min( color.g, color.b ) );
	float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;
	color -= offset;
	float peak = max( color.r, max( color.g, color.b ) );
	if ( peak < StartCompression ) return color;
	float d = 1. - StartCompression;
	float newPeak = 1. - d * d / ( peak + d - StartCompression );
	color *= newPeak / peak;
	float g = 1. - 1. / ( Desaturation * ( peak - newPeak ) + 1. );
	return mix( color, vec3( newPeak ), g );
}
vec3 CustomToneMapping( vec3 color ) { return color; }`,kw=`#ifdef USE_TRANSMISSION
	material.transmission = transmission;
	material.transmissionAlpha = 1.0;
	material.thickness = thickness;
	material.attenuationDistance = attenuationDistance;
	material.attenuationColor = attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		material.transmission *= texture2D( transmissionMap, vTransmissionMapUv ).r;
	#endif
	#ifdef USE_THICKNESSMAP
		material.thickness *= texture2D( thicknessMap, vThicknessMapUv ).g;
	#endif
	vec3 pos = vWorldPosition;
	vec3 v = normalize( cameraPosition - pos );
	vec3 n = inverseTransformDirection( normal, viewMatrix );
	vec4 transmitted = getIBLVolumeRefraction(
		n, v, material.roughness, material.diffuseColor, material.specularColor, material.specularF90,
		pos, modelMatrix, viewMatrix, projectionMatrix, material.dispersion, material.ior, material.thickness,
		material.attenuationColor, material.attenuationDistance );
	material.transmissionAlpha = mix( material.transmissionAlpha, transmitted.a, material.transmission );
	totalDiffuse = mix( totalDiffuse, transmitted.rgb, material.transmission );
#endif`,Bw=`#ifdef USE_TRANSMISSION
	uniform float transmission;
	uniform float thickness;
	uniform float attenuationDistance;
	uniform vec3 attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		uniform sampler2D transmissionMap;
	#endif
	#ifdef USE_THICKNESSMAP
		uniform sampler2D thicknessMap;
	#endif
	uniform vec2 transmissionSamplerSize;
	uniform sampler2D transmissionSamplerMap;
	uniform mat4 modelMatrix;
	uniform mat4 projectionMatrix;
	varying vec3 vWorldPosition;
	float w0( float a ) {
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - a + 3.0 ) - 3.0 ) + 1.0 );
	}
	float w1( float a ) {
		return ( 1.0 / 6.0 ) * ( a *  a * ( 3.0 * a - 6.0 ) + 4.0 );
	}
	float w2( float a ){
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - 3.0 * a + 3.0 ) + 3.0 ) + 1.0 );
	}
	float w3( float a ) {
		return ( 1.0 / 6.0 ) * ( a * a * a );
	}
	float g0( float a ) {
		return w0( a ) + w1( a );
	}
	float g1( float a ) {
		return w2( a ) + w3( a );
	}
	float h0( float a ) {
		return - 1.0 + w1( a ) / ( w0( a ) + w1( a ) );
	}
	float h1( float a ) {
		return 1.0 + w3( a ) / ( w2( a ) + w3( a ) );
	}
	vec4 bicubic( sampler2D tex, vec2 uv, vec4 texelSize, float lod ) {
		uv = uv * texelSize.zw + 0.5;
		vec2 iuv = floor( uv );
		vec2 fuv = fract( uv );
		float g0x = g0( fuv.x );
		float g1x = g1( fuv.x );
		float h0x = h0( fuv.x );
		float h1x = h1( fuv.x );
		float h0y = h0( fuv.y );
		float h1y = h1( fuv.y );
		vec2 p0 = ( vec2( iuv.x + h0x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p1 = ( vec2( iuv.x + h1x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p2 = ( vec2( iuv.x + h0x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		vec2 p3 = ( vec2( iuv.x + h1x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		return g0( fuv.y ) * ( g0x * textureLod( tex, p0, lod ) + g1x * textureLod( tex, p1, lod ) ) +
			g1( fuv.y ) * ( g0x * textureLod( tex, p2, lod ) + g1x * textureLod( tex, p3, lod ) );
	}
	vec4 textureBicubic( sampler2D sampler, vec2 uv, float lod ) {
		vec2 fLodSize = vec2( textureSize( sampler, int( lod ) ) );
		vec2 cLodSize = vec2( textureSize( sampler, int( lod + 1.0 ) ) );
		vec2 fLodSizeInv = 1.0 / fLodSize;
		vec2 cLodSizeInv = 1.0 / cLodSize;
		vec4 fSample = bicubic( sampler, uv, vec4( fLodSizeInv, fLodSize ), floor( lod ) );
		vec4 cSample = bicubic( sampler, uv, vec4( cLodSizeInv, cLodSize ), ceil( lod ) );
		return mix( fSample, cSample, fract( lod ) );
	}
	vec3 getVolumeTransmissionRay( const in vec3 n, const in vec3 v, const in float thickness, const in float ior, const in mat4 modelMatrix ) {
		vec3 refractionVector = refract( - v, normalize( n ), 1.0 / ior );
		vec3 modelScale;
		modelScale.x = length( vec3( modelMatrix[ 0 ].xyz ) );
		modelScale.y = length( vec3( modelMatrix[ 1 ].xyz ) );
		modelScale.z = length( vec3( modelMatrix[ 2 ].xyz ) );
		return normalize( refractionVector ) * thickness * modelScale;
	}
	float applyIorToRoughness( const in float roughness, const in float ior ) {
		return roughness * clamp( ior * 2.0 - 2.0, 0.0, 1.0 );
	}
	vec4 getTransmissionSample( const in vec2 fragCoord, const in float roughness, const in float ior ) {
		float lod = log2( transmissionSamplerSize.x ) * applyIorToRoughness( roughness, ior );
		return textureBicubic( transmissionSamplerMap, fragCoord.xy, lod );
	}
	vec3 volumeAttenuation( const in float transmissionDistance, const in vec3 attenuationColor, const in float attenuationDistance ) {
		if ( isinf( attenuationDistance ) ) {
			return vec3( 1.0 );
		} else {
			vec3 attenuationCoefficient = -log( attenuationColor ) / attenuationDistance;
			vec3 transmittance = exp( - attenuationCoefficient * transmissionDistance );			return transmittance;
		}
	}
	vec4 getIBLVolumeRefraction( const in vec3 n, const in vec3 v, const in float roughness, const in vec3 diffuseColor,
		const in vec3 specularColor, const in float specularF90, const in vec3 position, const in mat4 modelMatrix,
		const in mat4 viewMatrix, const in mat4 projMatrix, const in float dispersion, const in float ior, const in float thickness,
		const in vec3 attenuationColor, const in float attenuationDistance ) {
		vec4 transmittedLight;
		vec3 transmittance;
		#ifdef USE_DISPERSION
			float halfSpread = ( ior - 1.0 ) * 0.025 * dispersion;
			vec3 iors = vec3( ior - halfSpread, ior, ior + halfSpread );
			for ( int i = 0; i < 3; i ++ ) {
				vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, iors[ i ], modelMatrix );
				vec3 refractedRayExit = position + transmissionRay;
		
				vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
				vec2 refractionCoords = ndcPos.xy / ndcPos.w;
				refractionCoords += 1.0;
				refractionCoords /= 2.0;
		
				vec4 transmissionSample = getTransmissionSample( refractionCoords, roughness, iors[ i ] );
				transmittedLight[ i ] = transmissionSample[ i ];
				transmittedLight.a += transmissionSample.a;
				transmittance[ i ] = diffuseColor[ i ] * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance )[ i ];
			}
			transmittedLight.a /= 3.0;
		
		#else
		
			vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, ior, modelMatrix );
			vec3 refractedRayExit = position + transmissionRay;
			vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
			vec2 refractionCoords = ndcPos.xy / ndcPos.w;
			refractionCoords += 1.0;
			refractionCoords /= 2.0;
			transmittedLight = getTransmissionSample( refractionCoords, roughness, ior );
			transmittance = diffuseColor * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance );
		
		#endif
		vec3 attenuatedColor = transmittance * transmittedLight.rgb;
		vec3 F = EnvironmentBRDF( n, v, specularColor, specularF90, roughness );
		float transmittanceFactor = ( transmittance.r + transmittance.g + transmittance.b ) / 3.0;
		return vec4( ( 1.0 - F ) * attenuatedColor, 1.0 - ( 1.0 - transmittedLight.a ) * transmittanceFactor );
	}
#endif`,zw=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_SPECULARMAP
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,Hw=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	uniform mat3 mapTransform;
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	uniform mat3 alphaMapTransform;
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	uniform mat3 lightMapTransform;
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	uniform mat3 aoMapTransform;
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	uniform mat3 bumpMapTransform;
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	uniform mat3 normalMapTransform;
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_DISPLACEMENTMAP
	uniform mat3 displacementMapTransform;
	varying vec2 vDisplacementMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	uniform mat3 emissiveMapTransform;
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	uniform mat3 metalnessMapTransform;
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	uniform mat3 roughnessMapTransform;
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	uniform mat3 anisotropyMapTransform;
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	uniform mat3 clearcoatMapTransform;
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform mat3 clearcoatNormalMapTransform;
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform mat3 clearcoatRoughnessMapTransform;
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	uniform mat3 sheenColorMapTransform;
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	uniform mat3 sheenRoughnessMapTransform;
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	uniform mat3 iridescenceMapTransform;
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform mat3 iridescenceThicknessMapTransform;
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SPECULARMAP
	uniform mat3 specularMapTransform;
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	uniform mat3 specularColorMapTransform;
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	uniform mat3 specularIntensityMapTransform;
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,Vw=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	vUv = vec3( uv, 1 ).xy;
#endif
#ifdef USE_MAP
	vMapUv = ( mapTransform * vec3( MAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ALPHAMAP
	vAlphaMapUv = ( alphaMapTransform * vec3( ALPHAMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_LIGHTMAP
	vLightMapUv = ( lightMapTransform * vec3( LIGHTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_AOMAP
	vAoMapUv = ( aoMapTransform * vec3( AOMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_BUMPMAP
	vBumpMapUv = ( bumpMapTransform * vec3( BUMPMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_NORMALMAP
	vNormalMapUv = ( normalMapTransform * vec3( NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_DISPLACEMENTMAP
	vDisplacementMapUv = ( displacementMapTransform * vec3( DISPLACEMENTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_EMISSIVEMAP
	vEmissiveMapUv = ( emissiveMapTransform * vec3( EMISSIVEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_METALNESSMAP
	vMetalnessMapUv = ( metalnessMapTransform * vec3( METALNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ROUGHNESSMAP
	vRoughnessMapUv = ( roughnessMapTransform * vec3( ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ANISOTROPYMAP
	vAnisotropyMapUv = ( anisotropyMapTransform * vec3( ANISOTROPYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOATMAP
	vClearcoatMapUv = ( clearcoatMapTransform * vec3( CLEARCOATMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	vClearcoatNormalMapUv = ( clearcoatNormalMapTransform * vec3( CLEARCOAT_NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	vClearcoatRoughnessMapUv = ( clearcoatRoughnessMapTransform * vec3( CLEARCOAT_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCEMAP
	vIridescenceMapUv = ( iridescenceMapTransform * vec3( IRIDESCENCEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	vIridescenceThicknessMapUv = ( iridescenceThicknessMapTransform * vec3( IRIDESCENCE_THICKNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_COLORMAP
	vSheenColorMapUv = ( sheenColorMapTransform * vec3( SHEEN_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	vSheenRoughnessMapUv = ( sheenRoughnessMapTransform * vec3( SHEEN_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULARMAP
	vSpecularMapUv = ( specularMapTransform * vec3( SPECULARMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_COLORMAP
	vSpecularColorMapUv = ( specularColorMapTransform * vec3( SPECULAR_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	vSpecularIntensityMapUv = ( specularIntensityMapTransform * vec3( SPECULAR_INTENSITYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_TRANSMISSIONMAP
	vTransmissionMapUv = ( transmissionMapTransform * vec3( TRANSMISSIONMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_THICKNESSMAP
	vThicknessMapUv = ( thicknessMapTransform * vec3( THICKNESSMAP_UV, 1 ) ).xy;
#endif`,Gw=`#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_BATCHING
		worldPosition = batchingMatrix * worldPosition;
	#endif
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`;const jw=`varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`,Ww=`uniform sampler2D t2D;
uniform float backgroundIntensity;
varying vec2 vUv;
void main() {
	vec4 texColor = texture2D( t2D, vUv );
	#ifdef DECODE_VIDEO_TEXTURE
		texColor = vec4( mix( pow( texColor.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), texColor.rgb * 0.0773993808, vec3( lessThanEqual( texColor.rgb, vec3( 0.04045 ) ) ) ), texColor.w );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,Xw=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,$w=`#ifdef ENVMAP_TYPE_CUBE
	uniform samplerCube envMap;
#elif defined( ENVMAP_TYPE_CUBE_UV )
	uniform sampler2D envMap;
#endif
uniform float flipEnvMap;
uniform float backgroundBlurriness;
uniform float backgroundIntensity;
uniform mat3 backgroundRotation;
varying vec3 vWorldDirection;
#include <cube_uv_reflection_fragment>
void main() {
	#ifdef ENVMAP_TYPE_CUBE
		vec4 texColor = textureCube( envMap, backgroundRotation * vec3( flipEnvMap * vWorldDirection.x, vWorldDirection.yz ) );
	#elif defined( ENVMAP_TYPE_CUBE_UV )
		vec4 texColor = textureCubeUV( envMap, backgroundRotation * vWorldDirection, backgroundBlurriness );
	#else
		vec4 texColor = vec4( 0.0, 0.0, 0.0, 1.0 );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,Yw=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,qw=`uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
varying vec3 vWorldDirection;
void main() {
	vec4 texColor = textureCube( tCube, vec3( tFlip * vWorldDirection.x, vWorldDirection.yz ) );
	gl_FragColor = texColor;
	gl_FragColor.a *= opacity;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,Kw=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
varying vec2 vHighPrecisionZW;
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vHighPrecisionZW = gl_Position.zw;
}`,Zw=`#if DEPTH_PACKING == 3200
	uniform float opacity;
#endif
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
varying vec2 vHighPrecisionZW;
void main() {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#if DEPTH_PACKING == 3200
		diffuseColor.a = opacity;
	#endif
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <logdepthbuf_fragment>
	float fragCoordZ = 0.5 * vHighPrecisionZW[0] / vHighPrecisionZW[1] + 0.5;
	#if DEPTH_PACKING == 3200
		gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );
	#elif DEPTH_PACKING == 3201
		gl_FragColor = packDepthToRGBA( fragCoordZ );
	#elif DEPTH_PACKING == 3202
		gl_FragColor = vec4( packDepthToRGB( fragCoordZ ), 1.0 );
	#elif DEPTH_PACKING == 3203
		gl_FragColor = vec4( packDepthToRG( fragCoordZ ), 0.0, 1.0 );
	#endif
}`,Jw=`#define DISTANCE
varying vec3 vWorldPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <worldpos_vertex>
	#include <clipping_planes_vertex>
	vWorldPosition = worldPosition.xyz;
}`,Qw=`#define DISTANCE
uniform vec3 referencePosition;
uniform float nearDistance;
uniform float farDistance;
varying vec3 vWorldPosition;
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <clipping_planes_pars_fragment>
void main () {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	float dist = length( vWorldPosition - referencePosition );
	dist = ( dist - nearDistance ) / ( farDistance - nearDistance );
	dist = saturate( dist );
	gl_FragColor = packDepthToRGBA( dist );
}`,e1=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,t1=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,n1=`uniform float scale;
attribute float lineDistance;
varying float vLineDistance;
#include <common>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	vLineDistance = scale * lineDistance;
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,i1=`uniform vec3 diffuse;
uniform float opacity;
uniform float dashSize;
uniform float totalSize;
varying float vLineDistance;
#include <common>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	if ( mod( vLineDistance, totalSize ) > dashSize ) {
		discard;
	}
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,r1=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#if defined ( USE_ENVMAP ) || defined ( USE_SKINNING )
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinbase_vertex>
		#include <skinnormal_vertex>
		#include <defaultnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <fog_vertex>
}`,s1=`uniform vec3 diffuse;
uniform float opacity;
#ifndef FLAT_SHADED
	varying vec3 vNormal;
#endif
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		reflectedLight.indirectDiffuse += lightMapTexel.rgb * lightMapIntensity * RECIPROCAL_PI;
	#else
		reflectedLight.indirectDiffuse += vec3( 1.0 );
	#endif
	#include <aomap_fragment>
	reflectedLight.indirectDiffuse *= diffuseColor.rgb;
	vec3 outgoingLight = reflectedLight.indirectDiffuse;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,o1=`#define LAMBERT
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,a1=`#define LAMBERT
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_lambert_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_lambert_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,l1=`#define MATCAP
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <displacementmap_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
	vViewPosition = - mvPosition.xyz;
}`,c1=`#define MATCAP
uniform vec3 diffuse;
uniform float opacity;
uniform sampler2D matcap;
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	vec3 viewDir = normalize( vViewPosition );
	vec3 x = normalize( vec3( viewDir.z, 0.0, - viewDir.x ) );
	vec3 y = cross( viewDir, x );
	vec2 uv = vec2( dot( x, normal ), dot( y, normal ) ) * 0.495 + 0.5;
	#ifdef USE_MATCAP
		vec4 matcapColor = texture2D( matcap, uv );
	#else
		vec4 matcapColor = vec4( vec3( mix( 0.2, 0.8, uv.y ) ), 1.0 );
	#endif
	vec3 outgoingLight = diffuseColor.rgb * matcapColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,u1=`#define NORMAL
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	vViewPosition = - mvPosition.xyz;
#endif
}`,d1=`#define NORMAL
uniform float opacity;
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <packing>
#include <uv_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( 0.0, 0.0, 0.0, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	gl_FragColor = vec4( packNormalToRGB( normal ), diffuseColor.a );
	#ifdef OPAQUE
		gl_FragColor.a = 1.0;
	#endif
}`,h1=`#define PHONG
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,f1=`#define PHONG
uniform vec3 diffuse;
uniform vec3 emissive;
uniform vec3 specular;
uniform float shininess;
uniform float opacity;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_phong_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_phong_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + reflectedLight.directSpecular + reflectedLight.indirectSpecular + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,p1=`#define STANDARD
varying vec3 vViewPosition;
#ifdef USE_TRANSMISSION
	varying vec3 vWorldPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
#ifdef USE_TRANSMISSION
	vWorldPosition = worldPosition.xyz;
#endif
}`,m1=`#define STANDARD
#ifdef PHYSICAL
	#define IOR
	#define USE_SPECULAR
#endif
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float roughness;
uniform float metalness;
uniform float opacity;
#ifdef IOR
	uniform float ior;
#endif
#ifdef USE_SPECULAR
	uniform float specularIntensity;
	uniform vec3 specularColor;
	#ifdef USE_SPECULAR_COLORMAP
		uniform sampler2D specularColorMap;
	#endif
	#ifdef USE_SPECULAR_INTENSITYMAP
		uniform sampler2D specularIntensityMap;
	#endif
#endif
#ifdef USE_CLEARCOAT
	uniform float clearcoat;
	uniform float clearcoatRoughness;
#endif
#ifdef USE_DISPERSION
	uniform float dispersion;
#endif
#ifdef USE_IRIDESCENCE
	uniform float iridescence;
	uniform float iridescenceIOR;
	uniform float iridescenceThicknessMinimum;
	uniform float iridescenceThicknessMaximum;
#endif
#ifdef USE_SHEEN
	uniform vec3 sheenColor;
	uniform float sheenRoughness;
	#ifdef USE_SHEEN_COLORMAP
		uniform sampler2D sheenColorMap;
	#endif
	#ifdef USE_SHEEN_ROUGHNESSMAP
		uniform sampler2D sheenRoughnessMap;
	#endif
#endif
#ifdef USE_ANISOTROPY
	uniform vec2 anisotropyVector;
	#ifdef USE_ANISOTROPYMAP
		uniform sampler2D anisotropyMap;
	#endif
#endif
varying vec3 vViewPosition;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <iridescence_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_physical_pars_fragment>
#include <transmission_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <clearcoat_pars_fragment>
#include <iridescence_pars_fragment>
#include <roughnessmap_pars_fragment>
#include <metalnessmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <roughnessmap_fragment>
	#include <metalnessmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <clearcoat_normal_fragment_begin>
	#include <clearcoat_normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_physical_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 totalDiffuse = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse;
	vec3 totalSpecular = reflectedLight.directSpecular + reflectedLight.indirectSpecular;
	#include <transmission_fragment>
	vec3 outgoingLight = totalDiffuse + totalSpecular + totalEmissiveRadiance;
	#ifdef USE_SHEEN
		float sheenEnergyComp = 1.0 - 0.157 * max3( material.sheenColor );
		outgoingLight = outgoingLight * sheenEnergyComp + sheenSpecularDirect + sheenSpecularIndirect;
	#endif
	#ifdef USE_CLEARCOAT
		float dotNVcc = saturate( dot( geometryClearcoatNormal, geometryViewDir ) );
		vec3 Fcc = F_Schlick( material.clearcoatF0, material.clearcoatF90, dotNVcc );
		outgoingLight = outgoingLight * ( 1.0 - material.clearcoat * Fcc ) + ( clearcoatSpecularDirect + clearcoatSpecularIndirect ) * material.clearcoat;
	#endif
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,g1=`#define TOON
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,_1=`#define TOON
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <gradientmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_toon_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_toon_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,v1=`uniform float size;
uniform float scale;
#include <common>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
#ifdef USE_POINTS_UV
	varying vec2 vUv;
	uniform mat3 uvTransform;
#endif
void main() {
	#ifdef USE_POINTS_UV
		vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	#endif
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	gl_PointSize = size;
	#ifdef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) gl_PointSize *= ( scale / - mvPosition.z );
	#endif
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <fog_vertex>
}`,x1=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <color_pars_fragment>
#include <map_particle_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_particle_fragment>
	#include <color_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,y1=`#include <common>
#include <batching_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <shadowmap_pars_vertex>
void main() {
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,S1=`uniform vec3 color;
uniform float opacity;
#include <common>
#include <packing>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <logdepthbuf_pars_fragment>
#include <shadowmap_pars_fragment>
#include <shadowmask_pars_fragment>
void main() {
	#include <logdepthbuf_fragment>
	gl_FragColor = vec4( color, opacity * ( 1.0 - getShadowMask() ) );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
}`,M1=`uniform float rotation;
uniform vec2 center;
#include <common>
#include <uv_pars_vertex>
#include <fog_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	vec4 mvPosition = modelViewMatrix[ 3 ];
	vec2 scale = vec2( length( modelMatrix[ 0 ].xyz ), length( modelMatrix[ 1 ].xyz ) );
	#ifndef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) scale *= - mvPosition.z;
	#endif
	vec2 alignedPosition = ( position.xy - ( center - vec2( 0.5 ) ) ) * scale;
	vec2 rotatedPosition;
	rotatedPosition.x = cos( rotation ) * alignedPosition.x - sin( rotation ) * alignedPosition.y;
	rotatedPosition.y = sin( rotation ) * alignedPosition.x + cos( rotation ) * alignedPosition.y;
	mvPosition.xy += rotatedPosition;
	gl_Position = projectionMatrix * mvPosition;
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,E1=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
}`,Je={alphahash_fragment:WM,alphahash_pars_fragment:XM,alphamap_fragment:$M,alphamap_pars_fragment:YM,alphatest_fragment:qM,alphatest_pars_fragment:KM,aomap_fragment:ZM,aomap_pars_fragment:JM,batching_pars_vertex:QM,batching_vertex:eE,begin_vertex:tE,beginnormal_vertex:nE,bsdfs:iE,iridescence_fragment:rE,bumpmap_pars_fragment:sE,clipping_planes_fragment:oE,clipping_planes_pars_fragment:aE,clipping_planes_pars_vertex:lE,clipping_planes_vertex:cE,color_fragment:uE,color_pars_fragment:dE,color_pars_vertex:hE,color_vertex:fE,common:pE,cube_uv_reflection_fragment:mE,defaultnormal_vertex:gE,displacementmap_pars_vertex:_E,displacementmap_vertex:vE,emissivemap_fragment:xE,emissivemap_pars_fragment:yE,colorspace_fragment:SE,colorspace_pars_fragment:ME,envmap_fragment:EE,envmap_common_pars_fragment:wE,envmap_pars_fragment:TE,envmap_pars_vertex:AE,envmap_physical_pars_fragment:FE,envmap_vertex:CE,fog_vertex:bE,fog_pars_vertex:RE,fog_fragment:PE,fog_pars_fragment:LE,gradientmap_pars_fragment:NE,lightmap_pars_fragment:DE,lights_lambert_fragment:IE,lights_lambert_pars_fragment:UE,lights_pars_begin:OE,lights_toon_fragment:kE,lights_toon_pars_fragment:BE,lights_phong_fragment:zE,lights_phong_pars_fragment:HE,lights_physical_fragment:VE,lights_physical_pars_fragment:GE,lights_fragment_begin:jE,lights_fragment_maps:WE,lights_fragment_end:XE,logdepthbuf_fragment:$E,logdepthbuf_pars_fragment:YE,logdepthbuf_pars_vertex:qE,logdepthbuf_vertex:KE,map_fragment:ZE,map_pars_fragment:JE,map_particle_fragment:QE,map_particle_pars_fragment:ew,metalnessmap_fragment:tw,metalnessmap_pars_fragment:nw,morphinstance_vertex:iw,morphcolor_vertex:rw,morphnormal_vertex:sw,morphtarget_pars_vertex:ow,morphtarget_vertex:aw,normal_fragment_begin:lw,normal_fragment_maps:cw,normal_pars_fragment:uw,normal_pars_vertex:dw,normal_vertex:hw,normalmap_pars_fragment:fw,clearcoat_normal_fragment_begin:pw,clearcoat_normal_fragment_maps:mw,clearcoat_pars_fragment:gw,iridescence_pars_fragment:_w,opaque_fragment:vw,packing:xw,premultiplied_alpha_fragment:yw,project_vertex:Sw,dithering_fragment:Mw,dithering_pars_fragment:Ew,roughnessmap_fragment:ww,roughnessmap_pars_fragment:Tw,shadowmap_pars_fragment:Aw,shadowmap_pars_vertex:Cw,shadowmap_vertex:bw,shadowmask_pars_fragment:Rw,skinbase_vertex:Pw,skinning_pars_vertex:Lw,skinning_vertex:Nw,skinnormal_vertex:Dw,specularmap_fragment:Iw,specularmap_pars_fragment:Uw,tonemapping_fragment:Ow,tonemapping_pars_fragment:Fw,transmission_fragment:kw,transmission_pars_fragment:Bw,uv_pars_fragment:zw,uv_pars_vertex:Hw,uv_vertex:Vw,worldpos_vertex:Gw,background_vert:jw,background_frag:Ww,backgroundCube_vert:Xw,backgroundCube_frag:$w,cube_vert:Yw,cube_frag:qw,depth_vert:Kw,depth_frag:Zw,distanceRGBA_vert:Jw,distanceRGBA_frag:Qw,equirect_vert:e1,equirect_frag:t1,linedashed_vert:n1,linedashed_frag:i1,meshbasic_vert:r1,meshbasic_frag:s1,meshlambert_vert:o1,meshlambert_frag:a1,meshmatcap_vert:l1,meshmatcap_frag:c1,meshnormal_vert:u1,meshnormal_frag:d1,meshphong_vert:h1,meshphong_frag:f1,meshphysical_vert:p1,meshphysical_frag:m1,meshtoon_vert:g1,meshtoon_frag:_1,points_vert:v1,points_frag:x1,shadow_vert:y1,shadow_frag:S1,sprite_vert:M1,sprite_frag:E1},Ee={common:{diffuse:{value:new ct(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new Ze},alphaMap:{value:null},alphaMapTransform:{value:new Ze},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new Ze}},envmap:{envMap:{value:null},envMapRotation:{value:new Ze},flipEnvMap:{value:-1},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:.98}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new Ze}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new Ze}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new Ze},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new Ze},normalScale:{value:new Fe(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new Ze},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new Ze}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new Ze}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new Ze}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:25e-5},fogNear:{value:1},fogFar:{value:2e3},fogColor:{value:new ct(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMap:{value:[]},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotShadowMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMap:{value:[]},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null}},points:{diffuse:{value:new ct(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new Ze},alphaTest:{value:0},uvTransform:{value:new Ze}},sprite:{diffuse:{value:new ct(16777215)},opacity:{value:1},center:{value:new Fe(.5,.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new Ze},alphaMap:{value:null},alphaMapTransform:{value:new Ze},alphaTest:{value:0}}},oi={basic:{uniforms:nn([Ee.common,Ee.specularmap,Ee.envmap,Ee.aomap,Ee.lightmap,Ee.fog]),vertexShader:Je.meshbasic_vert,fragmentShader:Je.meshbasic_frag},lambert:{uniforms:nn([Ee.common,Ee.specularmap,Ee.envmap,Ee.aomap,Ee.lightmap,Ee.emissivemap,Ee.bumpmap,Ee.normalmap,Ee.displacementmap,Ee.fog,Ee.lights,{emissive:{value:new ct(0)}}]),vertexShader:Je.meshlambert_vert,fragmentShader:Je.meshlambert_frag},phong:{uniforms:nn([Ee.common,Ee.specularmap,Ee.envmap,Ee.aomap,Ee.lightmap,Ee.emissivemap,Ee.bumpmap,Ee.normalmap,Ee.displacementmap,Ee.fog,Ee.lights,{emissive:{value:new ct(0)},specular:{value:new ct(1118481)},shininess:{value:30}}]),vertexShader:Je.meshphong_vert,fragmentShader:Je.meshphong_frag},standard:{uniforms:nn([Ee.common,Ee.envmap,Ee.aomap,Ee.lightmap,Ee.emissivemap,Ee.bumpmap,Ee.normalmap,Ee.displacementmap,Ee.roughnessmap,Ee.metalnessmap,Ee.fog,Ee.lights,{emissive:{value:new ct(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:Je.meshphysical_vert,fragmentShader:Je.meshphysical_frag},toon:{uniforms:nn([Ee.common,Ee.aomap,Ee.lightmap,Ee.emissivemap,Ee.bumpmap,Ee.normalmap,Ee.displacementmap,Ee.gradientmap,Ee.fog,Ee.lights,{emissive:{value:new ct(0)}}]),vertexShader:Je.meshtoon_vert,fragmentShader:Je.meshtoon_frag},matcap:{uniforms:nn([Ee.common,Ee.bumpmap,Ee.normalmap,Ee.displacementmap,Ee.fog,{matcap:{value:null}}]),vertexShader:Je.meshmatcap_vert,fragmentShader:Je.meshmatcap_frag},points:{uniforms:nn([Ee.points,Ee.fog]),vertexShader:Je.points_vert,fragmentShader:Je.points_frag},dashed:{uniforms:nn([Ee.common,Ee.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:Je.linedashed_vert,fragmentShader:Je.linedashed_frag},depth:{uniforms:nn([Ee.common,Ee.displacementmap]),vertexShader:Je.depth_vert,fragmentShader:Je.depth_frag},normal:{uniforms:nn([Ee.common,Ee.bumpmap,Ee.normalmap,Ee.displacementmap,{opacity:{value:1}}]),vertexShader:Je.meshnormal_vert,fragmentShader:Je.meshnormal_frag},sprite:{uniforms:nn([Ee.sprite,Ee.fog]),vertexShader:Je.sprite_vert,fragmentShader:Je.sprite_frag},background:{uniforms:{uvTransform:{value:new Ze},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:Je.background_vert,fragmentShader:Je.background_frag},backgroundCube:{uniforms:{envMap:{value:null},flipEnvMap:{value:-1},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new Ze}},vertexShader:Je.backgroundCube_vert,fragmentShader:Je.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:Je.cube_vert,fragmentShader:Je.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:Je.equirect_vert,fragmentShader:Je.equirect_frag},distanceRGBA:{uniforms:nn([Ee.common,Ee.displacementmap,{referencePosition:{value:new O},nearDistance:{value:1},farDistance:{value:1e3}}]),vertexShader:Je.distanceRGBA_vert,fragmentShader:Je.distanceRGBA_frag},shadow:{uniforms:nn([Ee.lights,Ee.fog,{color:{value:new ct(0)},opacity:{value:1}}]),vertexShader:Je.shadow_vert,fragmentShader:Je.shadow_frag}};oi.physical={uniforms:nn([oi.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new Ze},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new Ze},clearcoatNormalScale:{value:new Fe(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new Ze},dispersion:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new Ze},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new Ze},sheen:{value:0},sheenColor:{value:new ct(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new Ze},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new Ze},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new Ze},transmissionSamplerSize:{value:new Fe},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new Ze},attenuationDistance:{value:0},attenuationColor:{value:new ct(0)},specularColor:{value:new ct(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new Ze},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new Ze},anisotropyVector:{value:new Fe},anisotropyMap:{value:null},anisotropyMapTransform:{value:new Ze}}]),vertexShader:Je.meshphysical_vert,fragmentShader:Je.meshphysical_frag};const el={r:0,b:0,g:0},Er=new hi,w1=new mt;function T1(t,e,n,i,r,s,o){const a=new ct(0);let l=s===!0?0:1,c,d,h=null,f=0,p=null;function g(v){let M=v.isScene===!0?v.background:null;return M&&M.isTexture&&(M=(v.backgroundBlurriness>0?n:e).get(M)),M}function x(v){let M=!1;const R=g(v);R===null?u(a,l):R&&R.isColor&&(u(R,1),M=!0);const C=t.xr.getEnvironmentBlendMode();C==="additive"?i.buffers.color.setClear(0,0,0,1,o):C==="alpha-blend"&&i.buffers.color.setClear(0,0,0,0,o),(t.autoClear||M)&&(i.buffers.depth.setTest(!0),i.buffers.depth.setMask(!0),i.buffers.color.setMask(!0),t.clear(t.autoClearColor,t.autoClearDepth,t.autoClearStencil))}function m(v,M){const R=g(M);R&&(R.isCubeTexture||R.mapping===yc)?(d===void 0&&(d=new Tn(new ca(1,1,1),new fr({name:"BackgroundCubeMaterial",uniforms:Ks(oi.backgroundCube.uniforms),vertexShader:oi.backgroundCube.vertexShader,fragmentShader:oi.backgroundCube.fragmentShader,side:gn,depthTest:!1,depthWrite:!1,fog:!1})),d.geometry.deleteAttribute("normal"),d.geometry.deleteAttribute("uv"),d.onBeforeRender=function(C,A,P){this.matrixWorld.copyPosition(P.matrixWorld)},Object.defineProperty(d.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),r.update(d)),Er.copy(M.backgroundRotation),Er.x*=-1,Er.y*=-1,Er.z*=-1,R.isCubeTexture&&R.isRenderTargetTexture===!1&&(Er.y*=-1,Er.z*=-1),d.material.uniforms.envMap.value=R,d.material.uniforms.flipEnvMap.value=R.isCubeTexture&&R.isRenderTargetTexture===!1?-1:1,d.material.uniforms.backgroundBlurriness.value=M.backgroundBlurriness,d.material.uniforms.backgroundIntensity.value=M.backgroundIntensity,d.material.uniforms.backgroundRotation.value.setFromMatrix4(w1.makeRotationFromEuler(Er)),d.material.toneMapped=lt.getTransfer(R.colorSpace)!==ft,(h!==R||f!==R.version||p!==t.toneMapping)&&(d.material.needsUpdate=!0,h=R,f=R.version,p=t.toneMapping),d.layers.enableAll(),v.unshift(d,d.geometry,d.material,0,0,null)):R&&R.isTexture&&(c===void 0&&(c=new Tn(new Ec(2,2),new fr({name:"BackgroundMaterial",uniforms:Ks(oi.background.uniforms),vertexShader:oi.background.vertexShader,fragmentShader:oi.background.fragmentShader,side:hr,depthTest:!1,depthWrite:!1,fog:!1})),c.geometry.deleteAttribute("normal"),Object.defineProperty(c.material,"map",{get:function(){return this.uniforms.t2D.value}}),r.update(c)),c.material.uniforms.t2D.value=R,c.material.uniforms.backgroundIntensity.value=M.backgroundIntensity,c.material.toneMapped=lt.getTransfer(R.colorSpace)!==ft,R.matrixAutoUpdate===!0&&R.updateMatrix(),c.material.uniforms.uvTransform.value.copy(R.matrix),(h!==R||f!==R.version||p!==t.toneMapping)&&(c.material.needsUpdate=!0,h=R,f=R.version,p=t.toneMapping),c.layers.enableAll(),v.unshift(c,c.geometry,c.material,0,0,null))}function u(v,M){v.getRGB(el,Wv(t)),i.buffers.color.setClear(el.r,el.g,el.b,M,o)}function _(){d!==void 0&&(d.geometry.dispose(),d.material.dispose()),c!==void 0&&(c.geometry.dispose(),c.material.dispose())}return{getClearColor:function(){return a},setClearColor:function(v,M=1){a.set(v),l=M,u(a,l)},getClearAlpha:function(){return l},setClearAlpha:function(v){l=v,u(a,l)},render:x,addToRenderList:m,dispose:_}}function A1(t,e){const n=t.getParameter(t.MAX_VERTEX_ATTRIBS),i={},r=f(null);let s=r,o=!1;function a(S,D,X,H,U){let Y=!1;const V=h(H,X,D);s!==V&&(s=V,c(s.object)),Y=p(S,H,X,U),Y&&g(S,H,X,U),U!==null&&e.update(U,t.ELEMENT_ARRAY_BUFFER),(Y||o)&&(o=!1,M(S,D,X,H),U!==null&&t.bindBuffer(t.ELEMENT_ARRAY_BUFFER,e.get(U).buffer))}function l(){return t.createVertexArray()}function c(S){return t.bindVertexArray(S)}function d(S){return t.deleteVertexArray(S)}function h(S,D,X){const H=X.wireframe===!0;let U=i[S.id];U===void 0&&(U={},i[S.id]=U);let Y=U[D.id];Y===void 0&&(Y={},U[D.id]=Y);let V=Y[H];return V===void 0&&(V=f(l()),Y[H]=V),V}function f(S){const D=[],X=[],H=[];for(let U=0;U<n;U++)D[U]=0,X[U]=0,H[U]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:D,enabledAttributes:X,attributeDivisors:H,object:S,attributes:{},index:null}}function p(S,D,X,H){const U=s.attributes,Y=D.attributes;let V=0;const J=X.getAttributes();for(const N in J)if(J[N].location>=0){const Z=U[N];let fe=Y[N];if(fe===void 0&&(N==="instanceMatrix"&&S.instanceMatrix&&(fe=S.instanceMatrix),N==="instanceColor"&&S.instanceColor&&(fe=S.instanceColor)),Z===void 0||Z.attribute!==fe||fe&&Z.data!==fe.data)return!0;V++}return s.attributesNum!==V||s.index!==H}function g(S,D,X,H){const U={},Y=D.attributes;let V=0;const J=X.getAttributes();for(const N in J)if(J[N].location>=0){let Z=Y[N];Z===void 0&&(N==="instanceMatrix"&&S.instanceMatrix&&(Z=S.instanceMatrix),N==="instanceColor"&&S.instanceColor&&(Z=S.instanceColor));const fe={};fe.attribute=Z,Z&&Z.data&&(fe.data=Z.data),U[N]=fe,V++}s.attributes=U,s.attributesNum=V,s.index=H}function x(){const S=s.newAttributes;for(let D=0,X=S.length;D<X;D++)S[D]=0}function m(S){u(S,0)}function u(S,D){const X=s.newAttributes,H=s.enabledAttributes,U=s.attributeDivisors;X[S]=1,H[S]===0&&(t.enableVertexAttribArray(S),H[S]=1),U[S]!==D&&(t.vertexAttribDivisor(S,D),U[S]=D)}function _(){const S=s.newAttributes,D=s.enabledAttributes;for(let X=0,H=D.length;X<H;X++)D[X]!==S[X]&&(t.disableVertexAttribArray(X),D[X]=0)}function v(S,D,X,H,U,Y,V){V===!0?t.vertexAttribIPointer(S,D,X,U,Y):t.vertexAttribPointer(S,D,X,H,U,Y)}function M(S,D,X,H){x();const U=H.attributes,Y=X.getAttributes(),V=D.defaultAttributeValues;for(const J in Y){const N=Y[J];if(N.location>=0){let j=U[J];if(j===void 0&&(J==="instanceMatrix"&&S.instanceMatrix&&(j=S.instanceMatrix),J==="instanceColor"&&S.instanceColor&&(j=S.instanceColor)),j!==void 0){const Z=j.normalized,fe=j.itemSize,_e=e.get(j);if(_e===void 0)continue;const Re=_e.buffer,I=_e.type,z=_e.bytesPerElement,ie=I===t.INT||I===t.UNSIGNED_INT||j.gpuType===Sf;if(j.isInterleavedBufferAttribute){const le=j.data,ye=le.stride,oe=j.offset;if(le.isInstancedInterleavedBuffer){for(let te=0;te<N.locationSize;te++)u(N.location+te,le.meshPerAttribute);S.isInstancedMesh!==!0&&H._maxInstanceCount===void 0&&(H._maxInstanceCount=le.meshPerAttribute*le.count)}else for(let te=0;te<N.locationSize;te++)m(N.location+te);t.bindBuffer(t.ARRAY_BUFFER,Re);for(let te=0;te<N.locationSize;te++)v(N.location+te,fe/N.locationSize,I,Z,ye*z,(oe+fe/N.locationSize*te)*z,ie)}else{if(j.isInstancedBufferAttribute){for(let le=0;le<N.locationSize;le++)u(N.location+le,j.meshPerAttribute);S.isInstancedMesh!==!0&&H._maxInstanceCount===void 0&&(H._maxInstanceCount=j.meshPerAttribute*j.count)}else for(let le=0;le<N.locationSize;le++)m(N.location+le);t.bindBuffer(t.ARRAY_BUFFER,Re);for(let le=0;le<N.locationSize;le++)v(N.location+le,fe/N.locationSize,I,Z,fe*z,fe/N.locationSize*le*z,ie)}}else if(V!==void 0){const Z=V[J];if(Z!==void 0)switch(Z.length){case 2:t.vertexAttrib2fv(N.location,Z);break;case 3:t.vertexAttrib3fv(N.location,Z);break;case 4:t.vertexAttrib4fv(N.location,Z);break;default:t.vertexAttrib1fv(N.location,Z)}}}}_()}function R(){P();for(const S in i){const D=i[S];for(const X in D){const H=D[X];for(const U in H)d(H[U].object),delete H[U];delete D[X]}delete i[S]}}function C(S){if(i[S.id]===void 0)return;const D=i[S.id];for(const X in D){const H=D[X];for(const U in H)d(H[U].object),delete H[U];delete D[X]}delete i[S.id]}function A(S){for(const D in i){const X=i[D];if(X[S.id]===void 0)continue;const H=X[S.id];for(const U in H)d(H[U].object),delete H[U];delete X[S.id]}}function P(){E(),o=!0,s!==r&&(s=r,c(s.object))}function E(){r.geometry=null,r.program=null,r.wireframe=!1}return{setup:a,reset:P,resetDefaultState:E,dispose:R,releaseStatesOfGeometry:C,releaseStatesOfProgram:A,initAttributes:x,enableAttribute:m,disableUnusedAttributes:_}}function C1(t,e,n){let i;function r(c){i=c}function s(c,d){t.drawArrays(i,c,d),n.update(d,i,1)}function o(c,d,h){h!==0&&(t.drawArraysInstanced(i,c,d,h),n.update(d,i,h))}function a(c,d,h){if(h===0)return;e.get("WEBGL_multi_draw").multiDrawArraysWEBGL(i,c,0,d,0,h);let p=0;for(let g=0;g<h;g++)p+=d[g];n.update(p,i,1)}function l(c,d,h,f){if(h===0)return;const p=e.get("WEBGL_multi_draw");if(p===null)for(let g=0;g<c.length;g++)o(c[g],d[g],f[g]);else{p.multiDrawArraysInstancedWEBGL(i,c,0,d,0,f,0,h);let g=0;for(let x=0;x<h;x++)g+=d[x]*f[x];n.update(g,i,1)}}this.setMode=r,this.render=s,this.renderInstances=o,this.renderMultiDraw=a,this.renderMultiDrawInstances=l}function b1(t,e,n,i){let r;function s(){if(r!==void 0)return r;if(e.has("EXT_texture_filter_anisotropic")===!0){const A=e.get("EXT_texture_filter_anisotropic");r=t.getParameter(A.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else r=0;return r}function o(A){return!(A!==Qn&&i.convert(A)!==t.getParameter(t.IMPLEMENTATION_COLOR_READ_FORMAT))}function a(A){const P=A===oa&&(e.has("EXT_color_buffer_half_float")||e.has("EXT_color_buffer_float"));return!(A!==Ui&&i.convert(A)!==t.getParameter(t.IMPLEMENTATION_COLOR_READ_TYPE)&&A!==Ci&&!P)}function l(A){if(A==="highp"){if(t.getShaderPrecisionFormat(t.VERTEX_SHADER,t.HIGH_FLOAT).precision>0&&t.getShaderPrecisionFormat(t.FRAGMENT_SHADER,t.HIGH_FLOAT).precision>0)return"highp";A="mediump"}return A==="mediump"&&t.getShaderPrecisionFormat(t.VERTEX_SHADER,t.MEDIUM_FLOAT).precision>0&&t.getShaderPrecisionFormat(t.FRAGMENT_SHADER,t.MEDIUM_FLOAT).precision>0?"mediump":"lowp"}let c=n.precision!==void 0?n.precision:"highp";const d=l(c);d!==c&&(console.warn("THREE.WebGLRenderer:",c,"not supported, using",d,"instead."),c=d);const h=n.logarithmicDepthBuffer===!0,f=n.reverseDepthBuffer===!0&&e.has("EXT_clip_control"),p=t.getParameter(t.MAX_TEXTURE_IMAGE_UNITS),g=t.getParameter(t.MAX_VERTEX_TEXTURE_IMAGE_UNITS),x=t.getParameter(t.MAX_TEXTURE_SIZE),m=t.getParameter(t.MAX_CUBE_MAP_TEXTURE_SIZE),u=t.getParameter(t.MAX_VERTEX_ATTRIBS),_=t.getParameter(t.MAX_VERTEX_UNIFORM_VECTORS),v=t.getParameter(t.MAX_VARYING_VECTORS),M=t.getParameter(t.MAX_FRAGMENT_UNIFORM_VECTORS),R=g>0,C=t.getParameter(t.MAX_SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:s,getMaxPrecision:l,textureFormatReadable:o,textureTypeReadable:a,precision:c,logarithmicDepthBuffer:h,reverseDepthBuffer:f,maxTextures:p,maxVertexTextures:g,maxTextureSize:x,maxCubemapSize:m,maxAttributes:u,maxVertexUniforms:_,maxVaryings:v,maxFragmentUniforms:M,vertexTextures:R,maxSamples:C}}function R1(t){const e=this;let n=null,i=0,r=!1,s=!1;const o=new Yi,a=new Ze,l={value:null,needsUpdate:!1};this.uniform=l,this.numPlanes=0,this.numIntersection=0,this.init=function(h,f){const p=h.length!==0||f||i!==0||r;return r=f,i=h.length,p},this.beginShadows=function(){s=!0,d(null)},this.endShadows=function(){s=!1},this.setGlobalState=function(h,f){n=d(h,f,0)},this.setState=function(h,f,p){const g=h.clippingPlanes,x=h.clipIntersection,m=h.clipShadows,u=t.get(h);if(!r||g===null||g.length===0||s&&!m)s?d(null):c();else{const _=s?0:i,v=_*4;let M=u.clippingState||null;l.value=M,M=d(g,f,v,p);for(let R=0;R!==v;++R)M[R]=n[R];u.clippingState=M,this.numIntersection=x?this.numPlanes:0,this.numPlanes+=_}};function c(){l.value!==n&&(l.value=n,l.needsUpdate=i>0),e.numPlanes=i,e.numIntersection=0}function d(h,f,p,g){const x=h!==null?h.length:0;let m=null;if(x!==0){if(m=l.value,g!==!0||m===null){const u=p+x*4,_=f.matrixWorldInverse;a.getNormalMatrix(_),(m===null||m.length<u)&&(m=new Float32Array(u));for(let v=0,M=p;v!==x;++v,M+=4)o.copy(h[v]).applyMatrix4(_,a),o.normal.toArray(m,M),m[M+3]=o.constant}l.value=m,l.needsUpdate=!0}return e.numPlanes=x,e.numIntersection=0,m}}function P1(t){let e=new WeakMap;function n(o,a){return a===Wd?o.mapping=Ws:a===Xd&&(o.mapping=Xs),o}function i(o){if(o&&o.isTexture){const a=o.mapping;if(a===Wd||a===Xd)if(e.has(o)){const l=e.get(o).texture;return n(l,o.mapping)}else{const l=o.image;if(l&&l.height>0){const c=new gM(l.height);return c.fromEquirectangularTexture(t,o),e.set(o,c),o.addEventListener("dispose",r),n(c.texture,o.mapping)}else return null}}return o}function r(o){const a=o.target;a.removeEventListener("dispose",r);const l=e.get(a);l!==void 0&&(e.delete(a),l.dispose())}function s(){e=new WeakMap}return{get:i,dispose:s}}const As=4,Tm=[.125,.215,.35,.446,.526,.582],Rr=20,Pu=new Jv,Am=new ct;let Lu=null,Nu=0,Du=0,Iu=!1;const Cr=(1+Math.sqrt(5))/2,us=1/Cr,Cm=[new O(-Cr,us,0),new O(Cr,us,0),new O(-us,0,Cr),new O(us,0,Cr),new O(0,Cr,-us),new O(0,Cr,us),new O(-1,1,-1),new O(1,1,-1),new O(-1,1,1),new O(1,1,1)];class bm{constructor(e){this._renderer=e,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._lodPlanes=[],this._sizeLods=[],this._sigmas=[],this._blurMaterial=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._compileMaterial(this._blurMaterial)}fromScene(e,n=0,i=.1,r=100){Lu=this._renderer.getRenderTarget(),Nu=this._renderer.getActiveCubeFace(),Du=this._renderer.getActiveMipmapLevel(),Iu=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(256);const s=this._allocateTargets();return s.depthBuffer=!0,this._sceneToCubeUV(e,i,r,s),n>0&&this._blur(s,0,0,n),this._applyPMREM(s),this._cleanup(s),s}fromEquirectangular(e,n=null){return this._fromTexture(e,n)}fromCubemap(e,n=null){return this._fromTexture(e,n)}compileCubemapShader(){this._cubemapMaterial===null&&(this._cubemapMaterial=Lm(),this._compileMaterial(this._cubemapMaterial))}compileEquirectangularShader(){this._equirectMaterial===null&&(this._equirectMaterial=Pm(),this._compileMaterial(this._equirectMaterial))}dispose(){this._dispose(),this._cubemapMaterial!==null&&this._cubemapMaterial.dispose(),this._equirectMaterial!==null&&this._equirectMaterial.dispose()}_setSize(e){this._lodMax=Math.floor(Math.log2(e)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){this._blurMaterial!==null&&this._blurMaterial.dispose(),this._pingPongRenderTarget!==null&&this._pingPongRenderTarget.dispose();for(let e=0;e<this._lodPlanes.length;e++)this._lodPlanes[e].dispose()}_cleanup(e){this._renderer.setRenderTarget(Lu,Nu,Du),this._renderer.xr.enabled=Iu,e.scissorTest=!1,tl(e,0,0,e.width,e.height)}_fromTexture(e,n){e.mapping===Ws||e.mapping===Xs?this._setSize(e.image.length===0?16:e.image[0].width||e.image[0].image.width):this._setSize(e.image.width/4),Lu=this._renderer.getRenderTarget(),Nu=this._renderer.getActiveCubeFace(),Du=this._renderer.getActiveMipmapLevel(),Iu=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;const i=n||this._allocateTargets();return this._textureToCubeUV(e,i),this._applyPMREM(i),this._cleanup(i),i}_allocateTargets(){const e=3*Math.max(this._cubeSize,112),n=4*this._cubeSize,i={magFilter:li,minFilter:li,generateMipmaps:!1,type:oa,format:Qn,colorSpace:qs,depthBuffer:!1},r=Rm(e,n,i);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==e||this._pingPongRenderTarget.height!==n){this._pingPongRenderTarget!==null&&this._dispose(),this._pingPongRenderTarget=Rm(e,n,i);const{_lodMax:s}=this;({sizeLods:this._sizeLods,lodPlanes:this._lodPlanes,sigmas:this._sigmas}=L1(s)),this._blurMaterial=N1(s,e,n)}return r}_compileMaterial(e){const n=new Tn(this._lodPlanes[0],e);this._renderer.compile(n,Pu)}_sceneToCubeUV(e,n,i,r){const a=new Fn(90,1,n,i),l=[1,-1,1,1,1,1],c=[1,1,1,-1,-1,-1],d=this._renderer,h=d.autoClear,f=d.toneMapping;d.getClearColor(Am),d.toneMapping=cr,d.autoClear=!1;const p=new Vv({name:"PMREM.Background",side:gn,depthWrite:!1,depthTest:!1}),g=new Tn(new ca,p);let x=!1;const m=e.background;m?m.isColor&&(p.color.copy(m),e.background=null,x=!0):(p.color.copy(Am),x=!0);for(let u=0;u<6;u++){const _=u%3;_===0?(a.up.set(0,l[u],0),a.lookAt(c[u],0,0)):_===1?(a.up.set(0,0,l[u]),a.lookAt(0,c[u],0)):(a.up.set(0,l[u],0),a.lookAt(0,0,c[u]));const v=this._cubeSize;tl(r,_*v,u>2?v:0,v,v),d.setRenderTarget(r),x&&d.render(g,a),d.render(e,a)}g.geometry.dispose(),g.material.dispose(),d.toneMapping=f,d.autoClear=h,e.background=m}_textureToCubeUV(e,n){const i=this._renderer,r=e.mapping===Ws||e.mapping===Xs;r?(this._cubemapMaterial===null&&(this._cubemapMaterial=Lm()),this._cubemapMaterial.uniforms.flipEnvMap.value=e.isRenderTargetTexture===!1?-1:1):this._equirectMaterial===null&&(this._equirectMaterial=Pm());const s=r?this._cubemapMaterial:this._equirectMaterial,o=new Tn(this._lodPlanes[0],s),a=s.uniforms;a.envMap.value=e;const l=this._cubeSize;tl(n,0,0,3*l,2*l),i.setRenderTarget(n),i.render(o,Pu)}_applyPMREM(e){const n=this._renderer,i=n.autoClear;n.autoClear=!1;const r=this._lodPlanes.length;for(let s=1;s<r;s++){const o=Math.sqrt(this._sigmas[s]*this._sigmas[s]-this._sigmas[s-1]*this._sigmas[s-1]),a=Cm[(r-s-1)%Cm.length];this._blur(e,s-1,s,o,a)}n.autoClear=i}_blur(e,n,i,r,s){const o=this._pingPongRenderTarget;this._halfBlur(e,o,n,i,r,"latitudinal",s),this._halfBlur(o,e,i,i,r,"longitudinal",s)}_halfBlur(e,n,i,r,s,o,a){const l=this._renderer,c=this._blurMaterial;o!=="latitudinal"&&o!=="longitudinal"&&console.error("blur direction must be either latitudinal or longitudinal!");const d=3,h=new Tn(this._lodPlanes[r],c),f=c.uniforms,p=this._sizeLods[i]-1,g=isFinite(s)?Math.PI/(2*p):2*Math.PI/(2*Rr-1),x=s/g,m=isFinite(s)?1+Math.floor(d*x):Rr;m>Rr&&console.warn(`sigmaRadians, ${s}, is too large and will clip, as it requested ${m} samples when the maximum is set to ${Rr}`);const u=[];let _=0;for(let A=0;A<Rr;++A){const P=A/x,E=Math.exp(-P*P/2);u.push(E),A===0?_+=E:A<m&&(_+=2*E)}for(let A=0;A<u.length;A++)u[A]=u[A]/_;f.envMap.value=e.texture,f.samples.value=m,f.weights.value=u,f.latitudinal.value=o==="latitudinal",a&&(f.poleAxis.value=a);const{_lodMax:v}=this;f.dTheta.value=g,f.mipInt.value=v-i;const M=this._sizeLods[r],R=3*M*(r>v-As?r-v+As:0),C=4*(this._cubeSize-M);tl(n,R,C,3*M,2*M),l.setRenderTarget(n),l.render(h,Pu)}}function L1(t){const e=[],n=[],i=[];let r=t;const s=t-As+1+Tm.length;for(let o=0;o<s;o++){const a=Math.pow(2,r);n.push(a);let l=1/a;o>t-As?l=Tm[o-t+As-1]:o===0&&(l=0),i.push(l);const c=1/(a-2),d=-c,h=1+c,f=[d,d,h,d,h,h,d,d,h,h,d,h],p=6,g=6,x=3,m=2,u=1,_=new Float32Array(x*g*p),v=new Float32Array(m*g*p),M=new Float32Array(u*g*p);for(let C=0;C<p;C++){const A=C%3*2/3-1,P=C>2?0:-1,E=[A,P,0,A+2/3,P,0,A+2/3,P+1,0,A,P,0,A+2/3,P+1,0,A,P+1,0];_.set(E,x*g*C),v.set(f,m*g*C);const S=[C,C,C,C,C,C];M.set(S,u*g*C)}const R=new Cn;R.setAttribute("position",new di(_,x)),R.setAttribute("uv",new di(v,m)),R.setAttribute("faceIndex",new di(M,u)),e.push(R),r>As&&r--}return{lodPlanes:e,sizeLods:n,sigmas:i}}function Rm(t,e,n){const i=new Gr(t,e,n);return i.texture.mapping=yc,i.texture.name="PMREM.cubeUv",i.scissorTest=!0,i}function tl(t,e,n,i,r){t.viewport.set(e,n,i,r),t.scissor.set(e,n,i,r)}function N1(t,e,n){const i=new Float32Array(Rr),r=new O(0,1,0);return new fr({name:"SphericalGaussianBlur",defines:{n:Rr,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/n,CUBEUV_MAX_MIP:`${t}.0`},uniforms:{envMap:{value:null},samples:{value:1},weights:{value:i},latitudinal:{value:!1},dTheta:{value:0},mipInt:{value:0},poleAxis:{value:r}},vertexShader:Lf(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform int samples;
			uniform float weights[ n ];
			uniform bool latitudinal;
			uniform float dTheta;
			uniform float mipInt;
			uniform vec3 poleAxis;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			vec3 getSample( float theta, vec3 axis ) {

				float cosTheta = cos( theta );
				// Rodrigues' axis-angle rotation
				vec3 sampleDirection = vOutputDirection * cosTheta
					+ cross( axis, vOutputDirection ) * sin( theta )
					+ axis * dot( axis, vOutputDirection ) * ( 1.0 - cosTheta );

				return bilinearCubeUV( envMap, sampleDirection, mipInt );

			}

			void main() {

				vec3 axis = latitudinal ? poleAxis : cross( poleAxis, vOutputDirection );

				if ( all( equal( axis, vec3( 0.0 ) ) ) ) {

					axis = vec3( vOutputDirection.z, 0.0, - vOutputDirection.x );

				}

				axis = normalize( axis );

				gl_FragColor = vec4( 0.0, 0.0, 0.0, 1.0 );
				gl_FragColor.rgb += weights[ 0 ] * getSample( 0.0, axis );

				for ( int i = 1; i < n; i++ ) {

					if ( i >= samples ) {

						break;

					}

					float theta = dTheta * float( i );
					gl_FragColor.rgb += weights[ i ] * getSample( -1.0 * theta, axis );
					gl_FragColor.rgb += weights[ i ] * getSample( theta, axis );

				}

			}
		`,blending:lr,depthTest:!1,depthWrite:!1})}function Pm(){return new fr({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:Lf(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;

			#include <common>

			void main() {

				vec3 outputDirection = normalize( vOutputDirection );
				vec2 uv = equirectUv( outputDirection );

				gl_FragColor = vec4( texture2D ( envMap, uv ).rgb, 1.0 );

			}
		`,blending:lr,depthTest:!1,depthWrite:!1})}function Lm(){return new fr({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:Lf(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:lr,depthTest:!1,depthWrite:!1})}function Lf(){return`

		precision mediump float;
		precision mediump int;

		attribute float faceIndex;

		varying vec3 vOutputDirection;

		// RH coordinate system; PMREM face-indexing convention
		vec3 getDirection( vec2 uv, float face ) {

			uv = 2.0 * uv - 1.0;

			vec3 direction = vec3( uv, 1.0 );

			if ( face == 0.0 ) {

				direction = direction.zyx; // ( 1, v, u ) pos x

			} else if ( face == 1.0 ) {

				direction = direction.xzy;
				direction.xz *= -1.0; // ( -u, 1, -v ) pos y

			} else if ( face == 2.0 ) {

				direction.x *= -1.0; // ( -u, v, 1 ) pos z

			} else if ( face == 3.0 ) {

				direction = direction.zyx;
				direction.xz *= -1.0; // ( -1, v, -u ) neg x

			} else if ( face == 4.0 ) {

				direction = direction.xzy;
				direction.xy *= -1.0; // ( -u, -1, v ) neg y

			} else if ( face == 5.0 ) {

				direction.z *= -1.0; // ( u, v, -1 ) neg z

			}

			return direction;

		}

		void main() {

			vOutputDirection = getDirection( uv, faceIndex );
			gl_Position = vec4( position, 1.0 );

		}
	`}function D1(t){let e=new WeakMap,n=null;function i(a){if(a&&a.isTexture){const l=a.mapping,c=l===Wd||l===Xd,d=l===Ws||l===Xs;if(c||d){let h=e.get(a);const f=h!==void 0?h.texture.pmremVersion:0;if(a.isRenderTargetTexture&&a.pmremVersion!==f)return n===null&&(n=new bm(t)),h=c?n.fromEquirectangular(a,h):n.fromCubemap(a,h),h.texture.pmremVersion=a.pmremVersion,e.set(a,h),h.texture;if(h!==void 0)return h.texture;{const p=a.image;return c&&p&&p.height>0||d&&p&&r(p)?(n===null&&(n=new bm(t)),h=c?n.fromEquirectangular(a):n.fromCubemap(a),h.texture.pmremVersion=a.pmremVersion,e.set(a,h),a.addEventListener("dispose",s),h.texture):null}}}return a}function r(a){let l=0;const c=6;for(let d=0;d<c;d++)a[d]!==void 0&&l++;return l===c}function s(a){const l=a.target;l.removeEventListener("dispose",s);const c=e.get(l);c!==void 0&&(e.delete(l),c.dispose())}function o(){e=new WeakMap,n!==null&&(n.dispose(),n=null)}return{get:i,dispose:o}}function I1(t){const e={};function n(i){if(e[i]!==void 0)return e[i];let r;switch(i){case"WEBGL_depth_texture":r=t.getExtension("WEBGL_depth_texture")||t.getExtension("MOZ_WEBGL_depth_texture")||t.getExtension("WEBKIT_WEBGL_depth_texture");break;case"EXT_texture_filter_anisotropic":r=t.getExtension("EXT_texture_filter_anisotropic")||t.getExtension("MOZ_EXT_texture_filter_anisotropic")||t.getExtension("WEBKIT_EXT_texture_filter_anisotropic");break;case"WEBGL_compressed_texture_s3tc":r=t.getExtension("WEBGL_compressed_texture_s3tc")||t.getExtension("MOZ_WEBGL_compressed_texture_s3tc")||t.getExtension("WEBKIT_WEBGL_compressed_texture_s3tc");break;case"WEBGL_compressed_texture_pvrtc":r=t.getExtension("WEBGL_compressed_texture_pvrtc")||t.getExtension("WEBKIT_WEBGL_compressed_texture_pvrtc");break;default:r=t.getExtension(i)}return e[i]=r,r}return{has:function(i){return n(i)!==null},init:function(){n("EXT_color_buffer_float"),n("WEBGL_clip_cull_distance"),n("OES_texture_float_linear"),n("EXT_color_buffer_half_float"),n("WEBGL_multisampled_render_to_texture"),n("WEBGL_render_shared_exponent")},get:function(i){const r=n(i);return r===null&&hs("THREE.WebGLRenderer: "+i+" extension not supported."),r}}}function U1(t,e,n,i){const r={},s=new WeakMap;function o(h){const f=h.target;f.index!==null&&e.remove(f.index);for(const g in f.attributes)e.remove(f.attributes[g]);f.removeEventListener("dispose",o),delete r[f.id];const p=s.get(f);p&&(e.remove(p),s.delete(f)),i.releaseStatesOfGeometry(f),f.isInstancedBufferGeometry===!0&&delete f._maxInstanceCount,n.memory.geometries--}function a(h,f){return r[f.id]===!0||(f.addEventListener("dispose",o),r[f.id]=!0,n.memory.geometries++),f}function l(h){const f=h.attributes;for(const p in f)e.update(f[p],t.ARRAY_BUFFER)}function c(h){const f=[],p=h.index,g=h.attributes.position;let x=0;if(p!==null){const _=p.array;x=p.version;for(let v=0,M=_.length;v<M;v+=3){const R=_[v+0],C=_[v+1],A=_[v+2];f.push(R,C,C,A,A,R)}}else if(g!==void 0){const _=g.array;x=g.version;for(let v=0,M=_.length/3-1;v<M;v+=3){const R=v+0,C=v+1,A=v+2;f.push(R,C,C,A,A,R)}}else return;const m=new(kv(f)?jv:Gv)(f,1);m.version=x;const u=s.get(h);u&&e.remove(u),s.set(h,m)}function d(h){const f=s.get(h);if(f){const p=h.index;p!==null&&f.version<p.version&&c(h)}else c(h);return s.get(h)}return{get:a,update:l,getWireframeAttribute:d}}function O1(t,e,n){let i;function r(f){i=f}let s,o;function a(f){s=f.type,o=f.bytesPerElement}function l(f,p){t.drawElements(i,p,s,f*o),n.update(p,i,1)}function c(f,p,g){g!==0&&(t.drawElementsInstanced(i,p,s,f*o,g),n.update(p,i,g))}function d(f,p,g){if(g===0)return;e.get("WEBGL_multi_draw").multiDrawElementsWEBGL(i,p,0,s,f,0,g);let m=0;for(let u=0;u<g;u++)m+=p[u];n.update(m,i,1)}function h(f,p,g,x){if(g===0)return;const m=e.get("WEBGL_multi_draw");if(m===null)for(let u=0;u<f.length;u++)c(f[u]/o,p[u],x[u]);else{m.multiDrawElementsInstancedWEBGL(i,p,0,s,f,0,x,0,g);let u=0;for(let _=0;_<g;_++)u+=p[_]*x[_];n.update(u,i,1)}}this.setMode=r,this.setIndex=a,this.render=l,this.renderInstances=c,this.renderMultiDraw=d,this.renderMultiDrawInstances=h}function F1(t){const e={geometries:0,textures:0},n={frame:0,calls:0,triangles:0,points:0,lines:0};function i(s,o,a){switch(n.calls++,o){case t.TRIANGLES:n.triangles+=a*(s/3);break;case t.LINES:n.lines+=a*(s/2);break;case t.LINE_STRIP:n.lines+=a*(s-1);break;case t.LINE_LOOP:n.lines+=a*s;break;case t.POINTS:n.points+=a*s;break;default:console.error("THREE.WebGLInfo: Unknown draw mode:",o);break}}function r(){n.calls=0,n.triangles=0,n.points=0,n.lines=0}return{memory:e,render:n,programs:null,autoReset:!0,reset:r,update:i}}function k1(t,e,n){const i=new WeakMap,r=new Rt;function s(o,a,l){const c=o.morphTargetInfluences,d=a.morphAttributes.position||a.morphAttributes.normal||a.morphAttributes.color,h=d!==void 0?d.length:0;let f=i.get(a);if(f===void 0||f.count!==h){let E=function(){A.dispose(),i.delete(a),a.removeEventListener("dispose",E)};f!==void 0&&f.texture.dispose();const p=a.morphAttributes.position!==void 0,g=a.morphAttributes.normal!==void 0,x=a.morphAttributes.color!==void 0,m=a.morphAttributes.position||[],u=a.morphAttributes.normal||[],_=a.morphAttributes.color||[];let v=0;p===!0&&(v=1),g===!0&&(v=2),x===!0&&(v=3);let M=a.attributes.position.count*v,R=1;M>e.maxTextureSize&&(R=Math.ceil(M/e.maxTextureSize),M=e.maxTextureSize);const C=new Float32Array(M*R*4*h),A=new zv(C,M,R,h);A.type=Ci,A.needsUpdate=!0;const P=v*4;for(let S=0;S<h;S++){const D=m[S],X=u[S],H=_[S],U=M*R*4*S;for(let Y=0;Y<D.count;Y++){const V=Y*P;p===!0&&(r.fromBufferAttribute(D,Y),C[U+V+0]=r.x,C[U+V+1]=r.y,C[U+V+2]=r.z,C[U+V+3]=0),g===!0&&(r.fromBufferAttribute(X,Y),C[U+V+4]=r.x,C[U+V+5]=r.y,C[U+V+6]=r.z,C[U+V+7]=0),x===!0&&(r.fromBufferAttribute(H,Y),C[U+V+8]=r.x,C[U+V+9]=r.y,C[U+V+10]=r.z,C[U+V+11]=H.itemSize===4?r.w:1)}}f={count:h,texture:A,size:new Fe(M,R)},i.set(a,f),a.addEventListener("dispose",E)}if(o.isInstancedMesh===!0&&o.morphTexture!==null)l.getUniforms().setValue(t,"morphTexture",o.morphTexture,n);else{let p=0;for(let x=0;x<c.length;x++)p+=c[x];const g=a.morphTargetsRelative?1:1-p;l.getUniforms().setValue(t,"morphTargetBaseInfluence",g),l.getUniforms().setValue(t,"morphTargetInfluences",c)}l.getUniforms().setValue(t,"morphTargetsTexture",f.texture,n),l.getUniforms().setValue(t,"morphTargetsTextureSize",f.size)}return{update:s}}function B1(t,e,n,i){let r=new WeakMap;function s(l){const c=i.render.frame,d=l.geometry,h=e.get(l,d);if(r.get(h)!==c&&(e.update(h),r.set(h,c)),l.isInstancedMesh&&(l.hasEventListener("dispose",a)===!1&&l.addEventListener("dispose",a),r.get(l)!==c&&(n.update(l.instanceMatrix,t.ARRAY_BUFFER),l.instanceColor!==null&&n.update(l.instanceColor,t.ARRAY_BUFFER),r.set(l,c))),l.isSkinnedMesh){const f=l.skeleton;r.get(f)!==c&&(f.update(),r.set(f,c))}return h}function o(){r=new WeakMap}function a(l){const c=l.target;c.removeEventListener("dispose",a),n.remove(c.instanceMatrix),c.instanceColor!==null&&n.remove(c.instanceColor)}return{update:s,dispose:o}}const e0=new _n,Nm=new Yv(1,1),t0=new zv,n0=new eM,i0=new $v,Dm=[],Im=[],Um=new Float32Array(16),Om=new Float32Array(9),Fm=new Float32Array(4);function to(t,e,n){const i=t[0];if(i<=0||i>0)return t;const r=e*n;let s=Dm[r];if(s===void 0&&(s=new Float32Array(r),Dm[r]=s),e!==0){i.toArray(s,0);for(let o=1,a=0;o!==e;++o)a+=n,t[o].toArray(s,a)}return s}function Bt(t,e){if(t.length!==e.length)return!1;for(let n=0,i=t.length;n<i;n++)if(t[n]!==e[n])return!1;return!0}function zt(t,e){for(let n=0,i=e.length;n<i;n++)t[n]=e[n]}function wc(t,e){let n=Im[e];n===void 0&&(n=new Int32Array(e),Im[e]=n);for(let i=0;i!==e;++i)n[i]=t.allocateTextureUnit();return n}function z1(t,e){const n=this.cache;n[0]!==e&&(t.uniform1f(this.addr,e),n[0]=e)}function H1(t,e){const n=this.cache;if(e.x!==void 0)(n[0]!==e.x||n[1]!==e.y)&&(t.uniform2f(this.addr,e.x,e.y),n[0]=e.x,n[1]=e.y);else{if(Bt(n,e))return;t.uniform2fv(this.addr,e),zt(n,e)}}function V1(t,e){const n=this.cache;if(e.x!==void 0)(n[0]!==e.x||n[1]!==e.y||n[2]!==e.z)&&(t.uniform3f(this.addr,e.x,e.y,e.z),n[0]=e.x,n[1]=e.y,n[2]=e.z);else if(e.r!==void 0)(n[0]!==e.r||n[1]!==e.g||n[2]!==e.b)&&(t.uniform3f(this.addr,e.r,e.g,e.b),n[0]=e.r,n[1]=e.g,n[2]=e.b);else{if(Bt(n,e))return;t.uniform3fv(this.addr,e),zt(n,e)}}function G1(t,e){const n=this.cache;if(e.x!==void 0)(n[0]!==e.x||n[1]!==e.y||n[2]!==e.z||n[3]!==e.w)&&(t.uniform4f(this.addr,e.x,e.y,e.z,e.w),n[0]=e.x,n[1]=e.y,n[2]=e.z,n[3]=e.w);else{if(Bt(n,e))return;t.uniform4fv(this.addr,e),zt(n,e)}}function j1(t,e){const n=this.cache,i=e.elements;if(i===void 0){if(Bt(n,e))return;t.uniformMatrix2fv(this.addr,!1,e),zt(n,e)}else{if(Bt(n,i))return;Fm.set(i),t.uniformMatrix2fv(this.addr,!1,Fm),zt(n,i)}}function W1(t,e){const n=this.cache,i=e.elements;if(i===void 0){if(Bt(n,e))return;t.uniformMatrix3fv(this.addr,!1,e),zt(n,e)}else{if(Bt(n,i))return;Om.set(i),t.uniformMatrix3fv(this.addr,!1,Om),zt(n,i)}}function X1(t,e){const n=this.cache,i=e.elements;if(i===void 0){if(Bt(n,e))return;t.uniformMatrix4fv(this.addr,!1,e),zt(n,e)}else{if(Bt(n,i))return;Um.set(i),t.uniformMatrix4fv(this.addr,!1,Um),zt(n,i)}}function $1(t,e){const n=this.cache;n[0]!==e&&(t.uniform1i(this.addr,e),n[0]=e)}function Y1(t,e){const n=this.cache;if(e.x!==void 0)(n[0]!==e.x||n[1]!==e.y)&&(t.uniform2i(this.addr,e.x,e.y),n[0]=e.x,n[1]=e.y);else{if(Bt(n,e))return;t.uniform2iv(this.addr,e),zt(n,e)}}function q1(t,e){const n=this.cache;if(e.x!==void 0)(n[0]!==e.x||n[1]!==e.y||n[2]!==e.z)&&(t.uniform3i(this.addr,e.x,e.y,e.z),n[0]=e.x,n[1]=e.y,n[2]=e.z);else{if(Bt(n,e))return;t.uniform3iv(this.addr,e),zt(n,e)}}function K1(t,e){const n=this.cache;if(e.x!==void 0)(n[0]!==e.x||n[1]!==e.y||n[2]!==e.z||n[3]!==e.w)&&(t.uniform4i(this.addr,e.x,e.y,e.z,e.w),n[0]=e.x,n[1]=e.y,n[2]=e.z,n[3]=e.w);else{if(Bt(n,e))return;t.uniform4iv(this.addr,e),zt(n,e)}}function Z1(t,e){const n=this.cache;n[0]!==e&&(t.uniform1ui(this.addr,e),n[0]=e)}function J1(t,e){const n=this.cache;if(e.x!==void 0)(n[0]!==e.x||n[1]!==e.y)&&(t.uniform2ui(this.addr,e.x,e.y),n[0]=e.x,n[1]=e.y);else{if(Bt(n,e))return;t.uniform2uiv(this.addr,e),zt(n,e)}}function Q1(t,e){const n=this.cache;if(e.x!==void 0)(n[0]!==e.x||n[1]!==e.y||n[2]!==e.z)&&(t.uniform3ui(this.addr,e.x,e.y,e.z),n[0]=e.x,n[1]=e.y,n[2]=e.z);else{if(Bt(n,e))return;t.uniform3uiv(this.addr,e),zt(n,e)}}function eT(t,e){const n=this.cache;if(e.x!==void 0)(n[0]!==e.x||n[1]!==e.y||n[2]!==e.z||n[3]!==e.w)&&(t.uniform4ui(this.addr,e.x,e.y,e.z,e.w),n[0]=e.x,n[1]=e.y,n[2]=e.z,n[3]=e.w);else{if(Bt(n,e))return;t.uniform4uiv(this.addr,e),zt(n,e)}}function tT(t,e,n){const i=this.cache,r=n.allocateTextureUnit();i[0]!==r&&(t.uniform1i(this.addr,r),i[0]=r);let s;this.type===t.SAMPLER_2D_SHADOW?(Nm.compareFunction=Fv,s=Nm):s=e0,n.setTexture2D(e||s,r)}function nT(t,e,n){const i=this.cache,r=n.allocateTextureUnit();i[0]!==r&&(t.uniform1i(this.addr,r),i[0]=r),n.setTexture3D(e||n0,r)}function iT(t,e,n){const i=this.cache,r=n.allocateTextureUnit();i[0]!==r&&(t.uniform1i(this.addr,r),i[0]=r),n.setTextureCube(e||i0,r)}function rT(t,e,n){const i=this.cache,r=n.allocateTextureUnit();i[0]!==r&&(t.uniform1i(this.addr,r),i[0]=r),n.setTexture2DArray(e||t0,r)}function sT(t){switch(t){case 5126:return z1;case 35664:return H1;case 35665:return V1;case 35666:return G1;case 35674:return j1;case 35675:return W1;case 35676:return X1;case 5124:case 35670:return $1;case 35667:case 35671:return Y1;case 35668:case 35672:return q1;case 35669:case 35673:return K1;case 5125:return Z1;case 36294:return J1;case 36295:return Q1;case 36296:return eT;case 35678:case 36198:case 36298:case 36306:case 35682:return tT;case 35679:case 36299:case 36307:return nT;case 35680:case 36300:case 36308:case 36293:return iT;case 36289:case 36303:case 36311:case 36292:return rT}}function oT(t,e){t.uniform1fv(this.addr,e)}function aT(t,e){const n=to(e,this.size,2);t.uniform2fv(this.addr,n)}function lT(t,e){const n=to(e,this.size,3);t.uniform3fv(this.addr,n)}function cT(t,e){const n=to(e,this.size,4);t.uniform4fv(this.addr,n)}function uT(t,e){const n=to(e,this.size,4);t.uniformMatrix2fv(this.addr,!1,n)}function dT(t,e){const n=to(e,this.size,9);t.uniformMatrix3fv(this.addr,!1,n)}function hT(t,e){const n=to(e,this.size,16);t.uniformMatrix4fv(this.addr,!1,n)}function fT(t,e){t.uniform1iv(this.addr,e)}function pT(t,e){t.uniform2iv(this.addr,e)}function mT(t,e){t.uniform3iv(this.addr,e)}function gT(t,e){t.uniform4iv(this.addr,e)}function _T(t,e){t.uniform1uiv(this.addr,e)}function vT(t,e){t.uniform2uiv(this.addr,e)}function xT(t,e){t.uniform3uiv(this.addr,e)}function yT(t,e){t.uniform4uiv(this.addr,e)}function ST(t,e,n){const i=this.cache,r=e.length,s=wc(n,r);Bt(i,s)||(t.uniform1iv(this.addr,s),zt(i,s));for(let o=0;o!==r;++o)n.setTexture2D(e[o]||e0,s[o])}function MT(t,e,n){const i=this.cache,r=e.length,s=wc(n,r);Bt(i,s)||(t.uniform1iv(this.addr,s),zt(i,s));for(let o=0;o!==r;++o)n.setTexture3D(e[o]||n0,s[o])}function ET(t,e,n){const i=this.cache,r=e.length,s=wc(n,r);Bt(i,s)||(t.uniform1iv(this.addr,s),zt(i,s));for(let o=0;o!==r;++o)n.setTextureCube(e[o]||i0,s[o])}function wT(t,e,n){const i=this.cache,r=e.length,s=wc(n,r);Bt(i,s)||(t.uniform1iv(this.addr,s),zt(i,s));for(let o=0;o!==r;++o)n.setTexture2DArray(e[o]||t0,s[o])}function TT(t){switch(t){case 5126:return oT;case 35664:return aT;case 35665:return lT;case 35666:return cT;case 35674:return uT;case 35675:return dT;case 35676:return hT;case 5124:case 35670:return fT;case 35667:case 35671:return pT;case 35668:case 35672:return mT;case 35669:case 35673:return gT;case 5125:return _T;case 36294:return vT;case 36295:return xT;case 36296:return yT;case 35678:case 36198:case 36298:case 36306:case 35682:return ST;case 35679:case 36299:case 36307:return MT;case 35680:case 36300:case 36308:case 36293:return ET;case 36289:case 36303:case 36311:case 36292:return wT}}class AT{constructor(e,n,i){this.id=e,this.addr=i,this.cache=[],this.type=n.type,this.setValue=sT(n.type)}}class CT{constructor(e,n,i){this.id=e,this.addr=i,this.cache=[],this.type=n.type,this.size=n.size,this.setValue=TT(n.type)}}class bT{constructor(e){this.id=e,this.seq=[],this.map={}}setValue(e,n,i){const r=this.seq;for(let s=0,o=r.length;s!==o;++s){const a=r[s];a.setValue(e,n[a.id],i)}}}const Uu=/(\w+)(\])?(\[|\.)?/g;function km(t,e){t.seq.push(e),t.map[e.id]=e}function RT(t,e,n){const i=t.name,r=i.length;for(Uu.lastIndex=0;;){const s=Uu.exec(i),o=Uu.lastIndex;let a=s[1];const l=s[2]==="]",c=s[3];if(l&&(a=a|0),c===void 0||c==="["&&o+2===r){km(n,c===void 0?new AT(a,t,e):new CT(a,t,e));break}else{let h=n.map[a];h===void 0&&(h=new bT(a),km(n,h)),n=h}}}class wl{constructor(e,n){this.seq=[],this.map={};const i=e.getProgramParameter(n,e.ACTIVE_UNIFORMS);for(let r=0;r<i;++r){const s=e.getActiveUniform(n,r),o=e.getUniformLocation(n,s.name);RT(s,o,this)}}setValue(e,n,i,r){const s=this.map[n];s!==void 0&&s.setValue(e,i,r)}setOptional(e,n,i){const r=n[i];r!==void 0&&this.setValue(e,i,r)}static upload(e,n,i,r){for(let s=0,o=n.length;s!==o;++s){const a=n[s],l=i[a.id];l.needsUpdate!==!1&&a.setValue(e,l.value,r)}}static seqWithValue(e,n){const i=[];for(let r=0,s=e.length;r!==s;++r){const o=e[r];o.id in n&&i.push(o)}return i}}function Bm(t,e,n){const i=t.createShader(e);return t.shaderSource(i,n),t.compileShader(i),i}const PT=37297;let LT=0;function NT(t,e){const n=t.split(`
`),i=[],r=Math.max(e-6,0),s=Math.min(e+6,n.length);for(let o=r;o<s;o++){const a=o+1;i.push(`${a===e?">":" "} ${a}: ${n[o]}`)}return i.join(`
`)}const zm=new Ze;function DT(t){lt._getMatrix(zm,lt.workingColorSpace,t);const e=`mat3( ${zm.elements.map(n=>n.toFixed(4))} )`;switch(lt.getTransfer(t)){case Kl:return[e,"LinearTransferOETF"];case ft:return[e,"sRGBTransferOETF"];default:return console.warn("THREE.WebGLProgram: Unsupported color space: ",t),[e,"LinearTransferOETF"]}}function Hm(t,e,n){const i=t.getShaderParameter(e,t.COMPILE_STATUS),r=t.getShaderInfoLog(e).trim();if(i&&r==="")return"";const s=/ERROR: 0:(\d+)/.exec(r);if(s){const o=parseInt(s[1]);return n.toUpperCase()+`

`+r+`

`+NT(t.getShaderSource(e),o)}else return r}function IT(t,e){const n=DT(e);return[`vec4 ${t}( vec4 value ) {`,`	return ${n[1]}( vec4( value.rgb * ${n[0]}, value.a ) );`,"}"].join(`
`)}function UT(t,e){let n;switch(e){case TS:n="Linear";break;case AS:n="Reinhard";break;case CS:n="Cineon";break;case bS:n="ACESFilmic";break;case PS:n="AgX";break;case LS:n="Neutral";break;case RS:n="Custom";break;default:console.warn("THREE.WebGLProgram: Unsupported toneMapping:",e),n="Linear"}return"vec3 "+t+"( vec3 color ) { return "+n+"ToneMapping( color ); }"}const nl=new O;function OT(){lt.getLuminanceCoefficients(nl);const t=nl.x.toFixed(4),e=nl.y.toFixed(4),n=nl.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${t}, ${e}, ${n} );`,"	return dot( weights, rgb );","}"].join(`
`)}function FT(t){return[t.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",t.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter(Eo).join(`
`)}function kT(t){const e=[];for(const n in t){const i=t[n];i!==!1&&e.push("#define "+n+" "+i)}return e.join(`
`)}function BT(t,e){const n={},i=t.getProgramParameter(e,t.ACTIVE_ATTRIBUTES);for(let r=0;r<i;r++){const s=t.getActiveAttrib(e,r),o=s.name;let a=1;s.type===t.FLOAT_MAT2&&(a=2),s.type===t.FLOAT_MAT3&&(a=3),s.type===t.FLOAT_MAT4&&(a=4),n[o]={type:s.type,location:t.getAttribLocation(e,o),locationSize:a}}return n}function Eo(t){return t!==""}function Vm(t,e){const n=e.numSpotLightShadows+e.numSpotLightMaps-e.numSpotLightShadowsWithMaps;return t.replace(/NUM_DIR_LIGHTS/g,e.numDirLights).replace(/NUM_SPOT_LIGHTS/g,e.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,e.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,n).replace(/NUM_RECT_AREA_LIGHTS/g,e.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,e.numPointLights).replace(/NUM_HEMI_LIGHTS/g,e.numHemiLights).replace(/NUM_DIR_LIGHT_SHADOWS/g,e.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,e.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,e.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,e.numPointLightShadows)}function Gm(t,e){return t.replace(/NUM_CLIPPING_PLANES/g,e.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,e.numClippingPlanes-e.numClipIntersection)}const zT=/^[ \t]*#include +<([\w\d./]+)>/gm;function Eh(t){return t.replace(zT,VT)}const HT=new Map;function VT(t,e){let n=Je[e];if(n===void 0){const i=HT.get(e);if(i!==void 0)n=Je[i],console.warn('THREE.WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',e,i);else throw new Error("Can not resolve #include <"+e+">")}return Eh(n)}const GT=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function jm(t){return t.replace(GT,jT)}function jT(t,e,n,i){let r="";for(let s=parseInt(e);s<parseInt(n);s++)r+=i.replace(/\[\s*i\s*\]/g,"[ "+s+" ]").replace(/UNROLLED_LOOP_INDEX/g,s);return r}function Wm(t){let e=`precision ${t.precision} float;
	precision ${t.precision} int;
	precision ${t.precision} sampler2D;
	precision ${t.precision} samplerCube;
	precision ${t.precision} sampler3D;
	precision ${t.precision} sampler2DArray;
	precision ${t.precision} sampler2DShadow;
	precision ${t.precision} samplerCubeShadow;
	precision ${t.precision} sampler2DArrayShadow;
	precision ${t.precision} isampler2D;
	precision ${t.precision} isampler3D;
	precision ${t.precision} isamplerCube;
	precision ${t.precision} isampler2DArray;
	precision ${t.precision} usampler2D;
	precision ${t.precision} usampler3D;
	precision ${t.precision} usamplerCube;
	precision ${t.precision} usampler2DArray;
	`;return t.precision==="highp"?e+=`
#define HIGH_PRECISION`:t.precision==="mediump"?e+=`
#define MEDIUM_PRECISION`:t.precision==="lowp"&&(e+=`
#define LOW_PRECISION`),e}function WT(t){let e="SHADOWMAP_TYPE_BASIC";return t.shadowMapType===Ev?e="SHADOWMAP_TYPE_PCF":t.shadowMapType===rS?e="SHADOWMAP_TYPE_PCF_SOFT":t.shadowMapType===Si&&(e="SHADOWMAP_TYPE_VSM"),e}function XT(t){let e="ENVMAP_TYPE_CUBE";if(t.envMap)switch(t.envMapMode){case Ws:case Xs:e="ENVMAP_TYPE_CUBE";break;case yc:e="ENVMAP_TYPE_CUBE_UV";break}return e}function $T(t){let e="ENVMAP_MODE_REFLECTION";if(t.envMap)switch(t.envMapMode){case Xs:e="ENVMAP_MODE_REFRACTION";break}return e}function YT(t){let e="ENVMAP_BLENDING_NONE";if(t.envMap)switch(t.combine){case wv:e="ENVMAP_BLENDING_MULTIPLY";break;case ES:e="ENVMAP_BLENDING_MIX";break;case wS:e="ENVMAP_BLENDING_ADD";break}return e}function qT(t){const e=t.envMapCubeUVHeight;if(e===null)return null;const n=Math.log2(e)-2,i=1/e;return{texelWidth:1/(3*Math.max(Math.pow(2,n),7*16)),texelHeight:i,maxMip:n}}function KT(t,e,n,i){const r=t.getContext(),s=n.defines;let o=n.vertexShader,a=n.fragmentShader;const l=WT(n),c=XT(n),d=$T(n),h=YT(n),f=qT(n),p=FT(n),g=kT(s),x=r.createProgram();let m,u,_=n.glslVersion?"#version "+n.glslVersion+`
`:"";n.isRawShaderMaterial?(m=["#define SHADER_TYPE "+n.shaderType,"#define SHADER_NAME "+n.shaderName,g].filter(Eo).join(`
`),m.length>0&&(m+=`
`),u=["#define SHADER_TYPE "+n.shaderType,"#define SHADER_NAME "+n.shaderName,g].filter(Eo).join(`
`),u.length>0&&(u+=`
`)):(m=[Wm(n),"#define SHADER_TYPE "+n.shaderType,"#define SHADER_NAME "+n.shaderName,g,n.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",n.batching?"#define USE_BATCHING":"",n.batchingColor?"#define USE_BATCHING_COLOR":"",n.instancing?"#define USE_INSTANCING":"",n.instancingColor?"#define USE_INSTANCING_COLOR":"",n.instancingMorph?"#define USE_INSTANCING_MORPH":"",n.useFog&&n.fog?"#define USE_FOG":"",n.useFog&&n.fogExp2?"#define FOG_EXP2":"",n.map?"#define USE_MAP":"",n.envMap?"#define USE_ENVMAP":"",n.envMap?"#define "+d:"",n.lightMap?"#define USE_LIGHTMAP":"",n.aoMap?"#define USE_AOMAP":"",n.bumpMap?"#define USE_BUMPMAP":"",n.normalMap?"#define USE_NORMALMAP":"",n.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",n.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",n.displacementMap?"#define USE_DISPLACEMENTMAP":"",n.emissiveMap?"#define USE_EMISSIVEMAP":"",n.anisotropy?"#define USE_ANISOTROPY":"",n.anisotropyMap?"#define USE_ANISOTROPYMAP":"",n.clearcoatMap?"#define USE_CLEARCOATMAP":"",n.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",n.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",n.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",n.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",n.specularMap?"#define USE_SPECULARMAP":"",n.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",n.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",n.roughnessMap?"#define USE_ROUGHNESSMAP":"",n.metalnessMap?"#define USE_METALNESSMAP":"",n.alphaMap?"#define USE_ALPHAMAP":"",n.alphaHash?"#define USE_ALPHAHASH":"",n.transmission?"#define USE_TRANSMISSION":"",n.transmissionMap?"#define USE_TRANSMISSIONMAP":"",n.thicknessMap?"#define USE_THICKNESSMAP":"",n.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",n.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",n.mapUv?"#define MAP_UV "+n.mapUv:"",n.alphaMapUv?"#define ALPHAMAP_UV "+n.alphaMapUv:"",n.lightMapUv?"#define LIGHTMAP_UV "+n.lightMapUv:"",n.aoMapUv?"#define AOMAP_UV "+n.aoMapUv:"",n.emissiveMapUv?"#define EMISSIVEMAP_UV "+n.emissiveMapUv:"",n.bumpMapUv?"#define BUMPMAP_UV "+n.bumpMapUv:"",n.normalMapUv?"#define NORMALMAP_UV "+n.normalMapUv:"",n.displacementMapUv?"#define DISPLACEMENTMAP_UV "+n.displacementMapUv:"",n.metalnessMapUv?"#define METALNESSMAP_UV "+n.metalnessMapUv:"",n.roughnessMapUv?"#define ROUGHNESSMAP_UV "+n.roughnessMapUv:"",n.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+n.anisotropyMapUv:"",n.clearcoatMapUv?"#define CLEARCOATMAP_UV "+n.clearcoatMapUv:"",n.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+n.clearcoatNormalMapUv:"",n.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+n.clearcoatRoughnessMapUv:"",n.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+n.iridescenceMapUv:"",n.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+n.iridescenceThicknessMapUv:"",n.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+n.sheenColorMapUv:"",n.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+n.sheenRoughnessMapUv:"",n.specularMapUv?"#define SPECULARMAP_UV "+n.specularMapUv:"",n.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+n.specularColorMapUv:"",n.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+n.specularIntensityMapUv:"",n.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+n.transmissionMapUv:"",n.thicknessMapUv?"#define THICKNESSMAP_UV "+n.thicknessMapUv:"",n.vertexTangents&&n.flatShading===!1?"#define USE_TANGENT":"",n.vertexColors?"#define USE_COLOR":"",n.vertexAlphas?"#define USE_COLOR_ALPHA":"",n.vertexUv1s?"#define USE_UV1":"",n.vertexUv2s?"#define USE_UV2":"",n.vertexUv3s?"#define USE_UV3":"",n.pointsUvs?"#define USE_POINTS_UV":"",n.flatShading?"#define FLAT_SHADED":"",n.skinning?"#define USE_SKINNING":"",n.morphTargets?"#define USE_MORPHTARGETS":"",n.morphNormals&&n.flatShading===!1?"#define USE_MORPHNORMALS":"",n.morphColors?"#define USE_MORPHCOLORS":"",n.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+n.morphTextureStride:"",n.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+n.morphTargetsCount:"",n.doubleSided?"#define DOUBLE_SIDED":"",n.flipSided?"#define FLIP_SIDED":"",n.shadowMapEnabled?"#define USE_SHADOWMAP":"",n.shadowMapEnabled?"#define "+l:"",n.sizeAttenuation?"#define USE_SIZEATTENUATION":"",n.numLightProbes>0?"#define USE_LIGHT_PROBES":"",n.logarithmicDepthBuffer?"#define USE_LOGDEPTHBUF":"",n.reverseDepthBuffer?"#define USE_REVERSEDEPTHBUF":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","	attribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","	attribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","	uniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","	attribute vec2 uv1;","#endif","#ifdef USE_UV2","	attribute vec2 uv2;","#endif","#ifdef USE_UV3","	attribute vec2 uv3;","#endif","#ifdef USE_TANGENT","	attribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","	attribute vec4 color;","#elif defined( USE_COLOR )","	attribute vec3 color;","#endif","#ifdef USE_SKINNING","	attribute vec4 skinIndex;","	attribute vec4 skinWeight;","#endif",`
`].filter(Eo).join(`
`),u=[Wm(n),"#define SHADER_TYPE "+n.shaderType,"#define SHADER_NAME "+n.shaderName,g,n.useFog&&n.fog?"#define USE_FOG":"",n.useFog&&n.fogExp2?"#define FOG_EXP2":"",n.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",n.map?"#define USE_MAP":"",n.matcap?"#define USE_MATCAP":"",n.envMap?"#define USE_ENVMAP":"",n.envMap?"#define "+c:"",n.envMap?"#define "+d:"",n.envMap?"#define "+h:"",f?"#define CUBEUV_TEXEL_WIDTH "+f.texelWidth:"",f?"#define CUBEUV_TEXEL_HEIGHT "+f.texelHeight:"",f?"#define CUBEUV_MAX_MIP "+f.maxMip+".0":"",n.lightMap?"#define USE_LIGHTMAP":"",n.aoMap?"#define USE_AOMAP":"",n.bumpMap?"#define USE_BUMPMAP":"",n.normalMap?"#define USE_NORMALMAP":"",n.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",n.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",n.emissiveMap?"#define USE_EMISSIVEMAP":"",n.anisotropy?"#define USE_ANISOTROPY":"",n.anisotropyMap?"#define USE_ANISOTROPYMAP":"",n.clearcoat?"#define USE_CLEARCOAT":"",n.clearcoatMap?"#define USE_CLEARCOATMAP":"",n.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",n.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",n.dispersion?"#define USE_DISPERSION":"",n.iridescence?"#define USE_IRIDESCENCE":"",n.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",n.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",n.specularMap?"#define USE_SPECULARMAP":"",n.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",n.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",n.roughnessMap?"#define USE_ROUGHNESSMAP":"",n.metalnessMap?"#define USE_METALNESSMAP":"",n.alphaMap?"#define USE_ALPHAMAP":"",n.alphaTest?"#define USE_ALPHATEST":"",n.alphaHash?"#define USE_ALPHAHASH":"",n.sheen?"#define USE_SHEEN":"",n.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",n.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",n.transmission?"#define USE_TRANSMISSION":"",n.transmissionMap?"#define USE_TRANSMISSIONMAP":"",n.thicknessMap?"#define USE_THICKNESSMAP":"",n.vertexTangents&&n.flatShading===!1?"#define USE_TANGENT":"",n.vertexColors||n.instancingColor||n.batchingColor?"#define USE_COLOR":"",n.vertexAlphas?"#define USE_COLOR_ALPHA":"",n.vertexUv1s?"#define USE_UV1":"",n.vertexUv2s?"#define USE_UV2":"",n.vertexUv3s?"#define USE_UV3":"",n.pointsUvs?"#define USE_POINTS_UV":"",n.gradientMap?"#define USE_GRADIENTMAP":"",n.flatShading?"#define FLAT_SHADED":"",n.doubleSided?"#define DOUBLE_SIDED":"",n.flipSided?"#define FLIP_SIDED":"",n.shadowMapEnabled?"#define USE_SHADOWMAP":"",n.shadowMapEnabled?"#define "+l:"",n.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",n.numLightProbes>0?"#define USE_LIGHT_PROBES":"",n.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",n.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",n.logarithmicDepthBuffer?"#define USE_LOGDEPTHBUF":"",n.reverseDepthBuffer?"#define USE_REVERSEDEPTHBUF":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",n.toneMapping!==cr?"#define TONE_MAPPING":"",n.toneMapping!==cr?Je.tonemapping_pars_fragment:"",n.toneMapping!==cr?UT("toneMapping",n.toneMapping):"",n.dithering?"#define DITHERING":"",n.opaque?"#define OPAQUE":"",Je.colorspace_pars_fragment,IT("linearToOutputTexel",n.outputColorSpace),OT(),n.useDepthPacking?"#define DEPTH_PACKING "+n.depthPacking:"",`
`].filter(Eo).join(`
`)),o=Eh(o),o=Vm(o,n),o=Gm(o,n),a=Eh(a),a=Vm(a,n),a=Gm(a,n),o=jm(o),a=jm(a),n.isRawShaderMaterial!==!0&&(_=`#version 300 es
`,m=[p,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+m,u=["#define varying in",n.glslVersion===Zp?"":"layout(location = 0) out highp vec4 pc_fragColor;",n.glslVersion===Zp?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+u);const v=_+m+o,M=_+u+a,R=Bm(r,r.VERTEX_SHADER,v),C=Bm(r,r.FRAGMENT_SHADER,M);r.attachShader(x,R),r.attachShader(x,C),n.index0AttributeName!==void 0?r.bindAttribLocation(x,0,n.index0AttributeName):n.morphTargets===!0&&r.bindAttribLocation(x,0,"position"),r.linkProgram(x);function A(D){if(t.debug.checkShaderErrors){const X=r.getProgramInfoLog(x).trim(),H=r.getShaderInfoLog(R).trim(),U=r.getShaderInfoLog(C).trim();let Y=!0,V=!0;if(r.getProgramParameter(x,r.LINK_STATUS)===!1)if(Y=!1,typeof t.debug.onShaderError=="function")t.debug.onShaderError(r,x,R,C);else{const J=Hm(r,R,"vertex"),N=Hm(r,C,"fragment");console.error("THREE.WebGLProgram: Shader Error "+r.getError()+" - VALIDATE_STATUS "+r.getProgramParameter(x,r.VALIDATE_STATUS)+`

Material Name: `+D.name+`
Material Type: `+D.type+`

Program Info Log: `+X+`
`+J+`
`+N)}else X!==""?console.warn("THREE.WebGLProgram: Program Info Log:",X):(H===""||U==="")&&(V=!1);V&&(D.diagnostics={runnable:Y,programLog:X,vertexShader:{log:H,prefix:m},fragmentShader:{log:U,prefix:u}})}r.deleteShader(R),r.deleteShader(C),P=new wl(r,x),E=BT(r,x)}let P;this.getUniforms=function(){return P===void 0&&A(this),P};let E;this.getAttributes=function(){return E===void 0&&A(this),E};let S=n.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){return S===!1&&(S=r.getProgramParameter(x,PT)),S},this.destroy=function(){i.releaseStatesOfProgram(this),r.deleteProgram(x),this.program=void 0},this.type=n.shaderType,this.name=n.shaderName,this.id=LT++,this.cacheKey=e,this.usedTimes=1,this.program=x,this.vertexShader=R,this.fragmentShader=C,this}let ZT=0;class JT{constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(e){const n=e.vertexShader,i=e.fragmentShader,r=this._getShaderStage(n),s=this._getShaderStage(i),o=this._getShaderCacheForMaterial(e);return o.has(r)===!1&&(o.add(r),r.usedTimes++),o.has(s)===!1&&(o.add(s),s.usedTimes++),this}remove(e){const n=this.materialCache.get(e);for(const i of n)i.usedTimes--,i.usedTimes===0&&this.shaderCache.delete(i.code);return this.materialCache.delete(e),this}getVertexShaderID(e){return this._getShaderStage(e.vertexShader).id}getFragmentShaderID(e){return this._getShaderStage(e.fragmentShader).id}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(e){const n=this.materialCache;let i=n.get(e);return i===void 0&&(i=new Set,n.set(e,i)),i}_getShaderStage(e){const n=this.shaderCache;let i=n.get(e);return i===void 0&&(i=new QT(e),n.set(e,i)),i}}class QT{constructor(e){this.id=ZT++,this.code=e,this.usedTimes=0}}function eA(t,e,n,i,r,s,o){const a=new Cf,l=new JT,c=new Set,d=[],h=r.logarithmicDepthBuffer,f=r.vertexTextures;let p=r.precision;const g={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distanceRGBA",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function x(E){return c.add(E),E===0?"uv":`uv${E}`}function m(E,S,D,X,H){const U=X.fog,Y=H.geometry,V=E.isMeshStandardMaterial?X.environment:null,J=(E.isMeshStandardMaterial?n:e).get(E.envMap||V),N=J&&J.mapping===yc?J.image.height:null,j=g[E.type];E.precision!==null&&(p=r.getMaxPrecision(E.precision),p!==E.precision&&console.warn("THREE.WebGLProgram.getParameters:",E.precision,"not supported, using",p,"instead."));const Z=Y.morphAttributes.position||Y.morphAttributes.normal||Y.morphAttributes.color,fe=Z!==void 0?Z.length:0;let _e=0;Y.morphAttributes.position!==void 0&&(_e=1),Y.morphAttributes.normal!==void 0&&(_e=2),Y.morphAttributes.color!==void 0&&(_e=3);let Re,I,z,ie;if(j){const it=oi[j];Re=it.vertexShader,I=it.fragmentShader}else Re=E.vertexShader,I=E.fragmentShader,l.update(E),z=l.getVertexShaderID(E),ie=l.getFragmentShaderID(E);const le=t.getRenderTarget(),ye=t.state.buffers.depth.getReversed(),oe=H.isInstancedMesh===!0,te=H.isBatchedMesh===!0,me=!!E.map,pe=!!E.matcap,Ue=!!J,L=!!E.aoMap,Xe=!!E.lightMap,ze=!!E.bumpMap,He=!!E.normalMap,Te=!!E.displacementMap,$e=!!E.emissiveMap,we=!!E.metalnessMap,b=!!E.roughnessMap,w=E.anisotropy>0,G=E.clearcoat>0,ne=E.dispersion>0,ae=E.iridescence>0,ee=E.sheen>0,Ie=E.transmission>0,Se=w&&!!E.anisotropyMap,Pe=G&&!!E.clearcoatMap,tt=G&&!!E.clearcoatNormalMap,K=G&&!!E.clearcoatRoughnessMap,se=ae&&!!E.iridescenceMap,ve=ae&&!!E.iridescenceThicknessMap,Me=ee&&!!E.sheenColorMap,ue=ee&&!!E.sheenRoughnessMap,je=!!E.specularMap,Ve=!!E.specularColorMap,Qe=!!E.specularIntensityMap,F=Ie&&!!E.transmissionMap,xe=Ie&&!!E.thicknessMap,q=!!E.gradientMap,re=!!E.alphaMap,be=E.alphaTest>0,Ae=!!E.alphaHash,Ke=!!E.extensions;let xt=cr;E.toneMapped&&(le===null||le.isXRRenderTarget===!0)&&(xt=t.toneMapping);const Lt={shaderID:j,shaderType:E.type,shaderName:E.name,vertexShader:Re,fragmentShader:I,defines:E.defines,customVertexShaderID:z,customFragmentShaderID:ie,isRawShaderMaterial:E.isRawShaderMaterial===!0,glslVersion:E.glslVersion,precision:p,batching:te,batchingColor:te&&H._colorsTexture!==null,instancing:oe,instancingColor:oe&&H.instanceColor!==null,instancingMorph:oe&&H.morphTexture!==null,supportsVertexTextures:f,outputColorSpace:le===null?t.outputColorSpace:le.isXRRenderTarget===!0?le.texture.colorSpace:qs,alphaToCoverage:!!E.alphaToCoverage,map:me,matcap:pe,envMap:Ue,envMapMode:Ue&&J.mapping,envMapCubeUVHeight:N,aoMap:L,lightMap:Xe,bumpMap:ze,normalMap:He,displacementMap:f&&Te,emissiveMap:$e,normalMapObjectSpace:He&&E.normalMapType===US,normalMapTangentSpace:He&&E.normalMapType===Ov,metalnessMap:we,roughnessMap:b,anisotropy:w,anisotropyMap:Se,clearcoat:G,clearcoatMap:Pe,clearcoatNormalMap:tt,clearcoatRoughnessMap:K,dispersion:ne,iridescence:ae,iridescenceMap:se,iridescenceThicknessMap:ve,sheen:ee,sheenColorMap:Me,sheenRoughnessMap:ue,specularMap:je,specularColorMap:Ve,specularIntensityMap:Qe,transmission:Ie,transmissionMap:F,thicknessMap:xe,gradientMap:q,opaque:E.transparent===!1&&E.blending===Is&&E.alphaToCoverage===!1,alphaMap:re,alphaTest:be,alphaHash:Ae,combine:E.combine,mapUv:me&&x(E.map.channel),aoMapUv:L&&x(E.aoMap.channel),lightMapUv:Xe&&x(E.lightMap.channel),bumpMapUv:ze&&x(E.bumpMap.channel),normalMapUv:He&&x(E.normalMap.channel),displacementMapUv:Te&&x(E.displacementMap.channel),emissiveMapUv:$e&&x(E.emissiveMap.channel),metalnessMapUv:we&&x(E.metalnessMap.channel),roughnessMapUv:b&&x(E.roughnessMap.channel),anisotropyMapUv:Se&&x(E.anisotropyMap.channel),clearcoatMapUv:Pe&&x(E.clearcoatMap.channel),clearcoatNormalMapUv:tt&&x(E.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:K&&x(E.clearcoatRoughnessMap.channel),iridescenceMapUv:se&&x(E.iridescenceMap.channel),iridescenceThicknessMapUv:ve&&x(E.iridescenceThicknessMap.channel),sheenColorMapUv:Me&&x(E.sheenColorMap.channel),sheenRoughnessMapUv:ue&&x(E.sheenRoughnessMap.channel),specularMapUv:je&&x(E.specularMap.channel),specularColorMapUv:Ve&&x(E.specularColorMap.channel),specularIntensityMapUv:Qe&&x(E.specularIntensityMap.channel),transmissionMapUv:F&&x(E.transmissionMap.channel),thicknessMapUv:xe&&x(E.thicknessMap.channel),alphaMapUv:re&&x(E.alphaMap.channel),vertexTangents:!!Y.attributes.tangent&&(He||w),vertexColors:E.vertexColors,vertexAlphas:E.vertexColors===!0&&!!Y.attributes.color&&Y.attributes.color.itemSize===4,pointsUvs:H.isPoints===!0&&!!Y.attributes.uv&&(me||re),fog:!!U,useFog:E.fog===!0,fogExp2:!!U&&U.isFogExp2,flatShading:E.flatShading===!0,sizeAttenuation:E.sizeAttenuation===!0,logarithmicDepthBuffer:h,reverseDepthBuffer:ye,skinning:H.isSkinnedMesh===!0,morphTargets:Y.morphAttributes.position!==void 0,morphNormals:Y.morphAttributes.normal!==void 0,morphColors:Y.morphAttributes.color!==void 0,morphTargetsCount:fe,morphTextureStride:_e,numDirLights:S.directional.length,numPointLights:S.point.length,numSpotLights:S.spot.length,numSpotLightMaps:S.spotLightMap.length,numRectAreaLights:S.rectArea.length,numHemiLights:S.hemi.length,numDirLightShadows:S.directionalShadowMap.length,numPointLightShadows:S.pointShadowMap.length,numSpotLightShadows:S.spotShadowMap.length,numSpotLightShadowsWithMaps:S.numSpotLightShadowsWithMaps,numLightProbes:S.numLightProbes,numClippingPlanes:o.numPlanes,numClipIntersection:o.numIntersection,dithering:E.dithering,shadowMapEnabled:t.shadowMap.enabled&&D.length>0,shadowMapType:t.shadowMap.type,toneMapping:xt,decodeVideoTexture:me&&E.map.isVideoTexture===!0&&lt.getTransfer(E.map.colorSpace)===ft,decodeVideoTextureEmissive:$e&&E.emissiveMap.isVideoTexture===!0&&lt.getTransfer(E.emissiveMap.colorSpace)===ft,premultipliedAlpha:E.premultipliedAlpha,doubleSided:E.side===wi,flipSided:E.side===gn,useDepthPacking:E.depthPacking>=0,depthPacking:E.depthPacking||0,index0AttributeName:E.index0AttributeName,extensionClipCullDistance:Ke&&E.extensions.clipCullDistance===!0&&i.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(Ke&&E.extensions.multiDraw===!0||te)&&i.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:i.has("KHR_parallel_shader_compile"),customProgramCacheKey:E.customProgramCacheKey()};return Lt.vertexUv1s=c.has(1),Lt.vertexUv2s=c.has(2),Lt.vertexUv3s=c.has(3),c.clear(),Lt}function u(E){const S=[];if(E.shaderID?S.push(E.shaderID):(S.push(E.customVertexShaderID),S.push(E.customFragmentShaderID)),E.defines!==void 0)for(const D in E.defines)S.push(D),S.push(E.defines[D]);return E.isRawShaderMaterial===!1&&(_(S,E),v(S,E),S.push(t.outputColorSpace)),S.push(E.customProgramCacheKey),S.join()}function _(E,S){E.push(S.precision),E.push(S.outputColorSpace),E.push(S.envMapMode),E.push(S.envMapCubeUVHeight),E.push(S.mapUv),E.push(S.alphaMapUv),E.push(S.lightMapUv),E.push(S.aoMapUv),E.push(S.bumpMapUv),E.push(S.normalMapUv),E.push(S.displacementMapUv),E.push(S.emissiveMapUv),E.push(S.metalnessMapUv),E.push(S.roughnessMapUv),E.push(S.anisotropyMapUv),E.push(S.clearcoatMapUv),E.push(S.clearcoatNormalMapUv),E.push(S.clearcoatRoughnessMapUv),E.push(S.iridescenceMapUv),E.push(S.iridescenceThicknessMapUv),E.push(S.sheenColorMapUv),E.push(S.sheenRoughnessMapUv),E.push(S.specularMapUv),E.push(S.specularColorMapUv),E.push(S.specularIntensityMapUv),E.push(S.transmissionMapUv),E.push(S.thicknessMapUv),E.push(S.combine),E.push(S.fogExp2),E.push(S.sizeAttenuation),E.push(S.morphTargetsCount),E.push(S.morphAttributeCount),E.push(S.numDirLights),E.push(S.numPointLights),E.push(S.numSpotLights),E.push(S.numSpotLightMaps),E.push(S.numHemiLights),E.push(S.numRectAreaLights),E.push(S.numDirLightShadows),E.push(S.numPointLightShadows),E.push(S.numSpotLightShadows),E.push(S.numSpotLightShadowsWithMaps),E.push(S.numLightProbes),E.push(S.shadowMapType),E.push(S.toneMapping),E.push(S.numClippingPlanes),E.push(S.numClipIntersection),E.push(S.depthPacking)}function v(E,S){a.disableAll(),S.supportsVertexTextures&&a.enable(0),S.instancing&&a.enable(1),S.instancingColor&&a.enable(2),S.instancingMorph&&a.enable(3),S.matcap&&a.enable(4),S.envMap&&a.enable(5),S.normalMapObjectSpace&&a.enable(6),S.normalMapTangentSpace&&a.enable(7),S.clearcoat&&a.enable(8),S.iridescence&&a.enable(9),S.alphaTest&&a.enable(10),S.vertexColors&&a.enable(11),S.vertexAlphas&&a.enable(12),S.vertexUv1s&&a.enable(13),S.vertexUv2s&&a.enable(14),S.vertexUv3s&&a.enable(15),S.vertexTangents&&a.enable(16),S.anisotropy&&a.enable(17),S.alphaHash&&a.enable(18),S.batching&&a.enable(19),S.dispersion&&a.enable(20),S.batchingColor&&a.enable(21),E.push(a.mask),a.disableAll(),S.fog&&a.enable(0),S.useFog&&a.enable(1),S.flatShading&&a.enable(2),S.logarithmicDepthBuffer&&a.enable(3),S.reverseDepthBuffer&&a.enable(4),S.skinning&&a.enable(5),S.morphTargets&&a.enable(6),S.morphNormals&&a.enable(7),S.morphColors&&a.enable(8),S.premultipliedAlpha&&a.enable(9),S.shadowMapEnabled&&a.enable(10),S.doubleSided&&a.enable(11),S.flipSided&&a.enable(12),S.useDepthPacking&&a.enable(13),S.dithering&&a.enable(14),S.transmission&&a.enable(15),S.sheen&&a.enable(16),S.opaque&&a.enable(17),S.pointsUvs&&a.enable(18),S.decodeVideoTexture&&a.enable(19),S.decodeVideoTextureEmissive&&a.enable(20),S.alphaToCoverage&&a.enable(21),E.push(a.mask)}function M(E){const S=g[E.type];let D;if(S){const X=oi[S];D=hM.clone(X.uniforms)}else D=E.uniforms;return D}function R(E,S){let D;for(let X=0,H=d.length;X<H;X++){const U=d[X];if(U.cacheKey===S){D=U,++D.usedTimes;break}}return D===void 0&&(D=new KT(t,S,E,s),d.push(D)),D}function C(E){if(--E.usedTimes===0){const S=d.indexOf(E);d[S]=d[d.length-1],d.pop(),E.destroy()}}function A(E){l.remove(E)}function P(){l.dispose()}return{getParameters:m,getProgramCacheKey:u,getUniforms:M,acquireProgram:R,releaseProgram:C,releaseShaderCache:A,programs:d,dispose:P}}function tA(){let t=new WeakMap;function e(o){return t.has(o)}function n(o){let a=t.get(o);return a===void 0&&(a={},t.set(o,a)),a}function i(o){t.delete(o)}function r(o,a,l){t.get(o)[a]=l}function s(){t=new WeakMap}return{has:e,get:n,remove:i,update:r,dispose:s}}function nA(t,e){return t.groupOrder!==e.groupOrder?t.groupOrder-e.groupOrder:t.renderOrder!==e.renderOrder?t.renderOrder-e.renderOrder:t.material.id!==e.material.id?t.material.id-e.material.id:t.z!==e.z?t.z-e.z:t.id-e.id}function Xm(t,e){return t.groupOrder!==e.groupOrder?t.groupOrder-e.groupOrder:t.renderOrder!==e.renderOrder?t.renderOrder-e.renderOrder:t.z!==e.z?e.z-t.z:t.id-e.id}function $m(){const t=[];let e=0;const n=[],i=[],r=[];function s(){e=0,n.length=0,i.length=0,r.length=0}function o(h,f,p,g,x,m){let u=t[e];return u===void 0?(u={id:h.id,object:h,geometry:f,material:p,groupOrder:g,renderOrder:h.renderOrder,z:x,group:m},t[e]=u):(u.id=h.id,u.object=h,u.geometry=f,u.material=p,u.groupOrder=g,u.renderOrder=h.renderOrder,u.z=x,u.group=m),e++,u}function a(h,f,p,g,x,m){const u=o(h,f,p,g,x,m);p.transmission>0?i.push(u):p.transparent===!0?r.push(u):n.push(u)}function l(h,f,p,g,x,m){const u=o(h,f,p,g,x,m);p.transmission>0?i.unshift(u):p.transparent===!0?r.unshift(u):n.unshift(u)}function c(h,f){n.length>1&&n.sort(h||nA),i.length>1&&i.sort(f||Xm),r.length>1&&r.sort(f||Xm)}function d(){for(let h=e,f=t.length;h<f;h++){const p=t[h];if(p.id===null)break;p.id=null,p.object=null,p.geometry=null,p.material=null,p.group=null}}return{opaque:n,transmissive:i,transparent:r,init:s,push:a,unshift:l,finish:d,sort:c}}function iA(){let t=new WeakMap;function e(i,r){const s=t.get(i);let o;return s===void 0?(o=new $m,t.set(i,[o])):r>=s.length?(o=new $m,s.push(o)):o=s[r],o}function n(){t=new WeakMap}return{get:e,dispose:n}}function rA(){const t={};return{get:function(e){if(t[e.id]!==void 0)return t[e.id];let n;switch(e.type){case"DirectionalLight":n={direction:new O,color:new ct};break;case"SpotLight":n={position:new O,direction:new O,color:new ct,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":n={position:new O,color:new ct,distance:0,decay:0};break;case"HemisphereLight":n={direction:new O,skyColor:new ct,groundColor:new ct};break;case"RectAreaLight":n={color:new ct,position:new O,halfWidth:new O,halfHeight:new O};break}return t[e.id]=n,n}}}function sA(){const t={};return{get:function(e){if(t[e.id]!==void 0)return t[e.id];let n;switch(e.type){case"DirectionalLight":n={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Fe};break;case"SpotLight":n={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Fe};break;case"PointLight":n={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Fe,shadowCameraNear:1,shadowCameraFar:1e3};break}return t[e.id]=n,n}}}let oA=0;function aA(t,e){return(e.castShadow?2:0)-(t.castShadow?2:0)+(e.map?1:0)-(t.map?1:0)}function lA(t){const e=new rA,n=sA(),i={version:0,hash:{directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let c=0;c<9;c++)i.probe.push(new O);const r=new O,s=new mt,o=new mt;function a(c){let d=0,h=0,f=0;for(let E=0;E<9;E++)i.probe[E].set(0,0,0);let p=0,g=0,x=0,m=0,u=0,_=0,v=0,M=0,R=0,C=0,A=0;c.sort(aA);for(let E=0,S=c.length;E<S;E++){const D=c[E],X=D.color,H=D.intensity,U=D.distance,Y=D.shadow&&D.shadow.map?D.shadow.map.texture:null;if(D.isAmbientLight)d+=X.r*H,h+=X.g*H,f+=X.b*H;else if(D.isLightProbe){for(let V=0;V<9;V++)i.probe[V].addScaledVector(D.sh.coefficients[V],H);A++}else if(D.isDirectionalLight){const V=e.get(D);if(V.color.copy(D.color).multiplyScalar(D.intensity),D.castShadow){const J=D.shadow,N=n.get(D);N.shadowIntensity=J.intensity,N.shadowBias=J.bias,N.shadowNormalBias=J.normalBias,N.shadowRadius=J.radius,N.shadowMapSize=J.mapSize,i.directionalShadow[p]=N,i.directionalShadowMap[p]=Y,i.directionalShadowMatrix[p]=D.shadow.matrix,_++}i.directional[p]=V,p++}else if(D.isSpotLight){const V=e.get(D);V.position.setFromMatrixPosition(D.matrixWorld),V.color.copy(X).multiplyScalar(H),V.distance=U,V.coneCos=Math.cos(D.angle),V.penumbraCos=Math.cos(D.angle*(1-D.penumbra)),V.decay=D.decay,i.spot[x]=V;const J=D.shadow;if(D.map&&(i.spotLightMap[R]=D.map,R++,J.updateMatrices(D),D.castShadow&&C++),i.spotLightMatrix[x]=J.matrix,D.castShadow){const N=n.get(D);N.shadowIntensity=J.intensity,N.shadowBias=J.bias,N.shadowNormalBias=J.normalBias,N.shadowRadius=J.radius,N.shadowMapSize=J.mapSize,i.spotShadow[x]=N,i.spotShadowMap[x]=Y,M++}x++}else if(D.isRectAreaLight){const V=e.get(D);V.color.copy(X).multiplyScalar(H),V.halfWidth.set(D.width*.5,0,0),V.halfHeight.set(0,D.height*.5,0),i.rectArea[m]=V,m++}else if(D.isPointLight){const V=e.get(D);if(V.color.copy(D.color).multiplyScalar(D.intensity),V.distance=D.distance,V.decay=D.decay,D.castShadow){const J=D.shadow,N=n.get(D);N.shadowIntensity=J.intensity,N.shadowBias=J.bias,N.shadowNormalBias=J.normalBias,N.shadowRadius=J.radius,N.shadowMapSize=J.mapSize,N.shadowCameraNear=J.camera.near,N.shadowCameraFar=J.camera.far,i.pointShadow[g]=N,i.pointShadowMap[g]=Y,i.pointShadowMatrix[g]=D.shadow.matrix,v++}i.point[g]=V,g++}else if(D.isHemisphereLight){const V=e.get(D);V.skyColor.copy(D.color).multiplyScalar(H),V.groundColor.copy(D.groundColor).multiplyScalar(H),i.hemi[u]=V,u++}}m>0&&(t.has("OES_texture_float_linear")===!0?(i.rectAreaLTC1=Ee.LTC_FLOAT_1,i.rectAreaLTC2=Ee.LTC_FLOAT_2):(i.rectAreaLTC1=Ee.LTC_HALF_1,i.rectAreaLTC2=Ee.LTC_HALF_2)),i.ambient[0]=d,i.ambient[1]=h,i.ambient[2]=f;const P=i.hash;(P.directionalLength!==p||P.pointLength!==g||P.spotLength!==x||P.rectAreaLength!==m||P.hemiLength!==u||P.numDirectionalShadows!==_||P.numPointShadows!==v||P.numSpotShadows!==M||P.numSpotMaps!==R||P.numLightProbes!==A)&&(i.directional.length=p,i.spot.length=x,i.rectArea.length=m,i.point.length=g,i.hemi.length=u,i.directionalShadow.length=_,i.directionalShadowMap.length=_,i.pointShadow.length=v,i.pointShadowMap.length=v,i.spotShadow.length=M,i.spotShadowMap.length=M,i.directionalShadowMatrix.length=_,i.pointShadowMatrix.length=v,i.spotLightMatrix.length=M+R-C,i.spotLightMap.length=R,i.numSpotLightShadowsWithMaps=C,i.numLightProbes=A,P.directionalLength=p,P.pointLength=g,P.spotLength=x,P.rectAreaLength=m,P.hemiLength=u,P.numDirectionalShadows=_,P.numPointShadows=v,P.numSpotShadows=M,P.numSpotMaps=R,P.numLightProbes=A,i.version=oA++)}function l(c,d){let h=0,f=0,p=0,g=0,x=0;const m=d.matrixWorldInverse;for(let u=0,_=c.length;u<_;u++){const v=c[u];if(v.isDirectionalLight){const M=i.directional[h];M.direction.setFromMatrixPosition(v.matrixWorld),r.setFromMatrixPosition(v.target.matrixWorld),M.direction.sub(r),M.direction.transformDirection(m),h++}else if(v.isSpotLight){const M=i.spot[p];M.position.setFromMatrixPosition(v.matrixWorld),M.position.applyMatrix4(m),M.direction.setFromMatrixPosition(v.matrixWorld),r.setFromMatrixPosition(v.target.matrixWorld),M.direction.sub(r),M.direction.transformDirection(m),p++}else if(v.isRectAreaLight){const M=i.rectArea[g];M.position.setFromMatrixPosition(v.matrixWorld),M.position.applyMatrix4(m),o.identity(),s.copy(v.matrixWorld),s.premultiply(m),o.extractRotation(s),M.halfWidth.set(v.width*.5,0,0),M.halfHeight.set(0,v.height*.5,0),M.halfWidth.applyMatrix4(o),M.halfHeight.applyMatrix4(o),g++}else if(v.isPointLight){const M=i.point[f];M.position.setFromMatrixPosition(v.matrixWorld),M.position.applyMatrix4(m),f++}else if(v.isHemisphereLight){const M=i.hemi[x];M.direction.setFromMatrixPosition(v.matrixWorld),M.direction.transformDirection(m),x++}}}return{setup:a,setupView:l,state:i}}function Ym(t){const e=new lA(t),n=[],i=[];function r(d){c.camera=d,n.length=0,i.length=0}function s(d){n.push(d)}function o(d){i.push(d)}function a(){e.setup(n)}function l(d){e.setupView(n,d)}const c={lightsArray:n,shadowsArray:i,camera:null,lights:e,transmissionRenderTarget:{}};return{init:r,state:c,setupLights:a,setupLightsView:l,pushLight:s,pushShadow:o}}function cA(t){let e=new WeakMap;function n(r,s=0){const o=e.get(r);let a;return o===void 0?(a=new Ym(t),e.set(r,[a])):s>=o.length?(a=new Ym(t),o.push(a)):a=o[s],a}function i(){e=new WeakMap}return{get:n,dispose:i}}const uA=`void main() {
	gl_Position = vec4( position, 1.0 );
}`,dA=`uniform sampler2D shadow_pass;
uniform vec2 resolution;
uniform float radius;
#include <packing>
void main() {
	const float samples = float( VSM_SAMPLES );
	float mean = 0.0;
	float squared_mean = 0.0;
	float uvStride = samples <= 1.0 ? 0.0 : 2.0 / ( samples - 1.0 );
	float uvStart = samples <= 1.0 ? 0.0 : - 1.0;
	for ( float i = 0.0; i < samples; i ++ ) {
		float uvOffset = uvStart + i * uvStride;
		#ifdef HORIZONTAL_PASS
			vec2 distribution = unpackRGBATo2Half( texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( uvOffset, 0.0 ) * radius ) / resolution ) );
			mean += distribution.x;
			squared_mean += distribution.y * distribution.y + distribution.x * distribution.x;
		#else
			float depth = unpackRGBAToDepth( texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( 0.0, uvOffset ) * radius ) / resolution ) );
			mean += depth;
			squared_mean += depth * depth;
		#endif
	}
	mean = mean / samples;
	squared_mean = squared_mean / samples;
	float std_dev = sqrt( squared_mean - mean * mean );
	gl_FragColor = pack2HalfToRGBA( vec2( mean, std_dev ) );
}`;function hA(t,e,n){let i=new bf;const r=new Fe,s=new Fe,o=new Rt,a=new UM({depthPacking:IS}),l=new OM,c={},d=n.maxTextureSize,h={[hr]:gn,[gn]:hr,[wi]:wi},f=new fr({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new Fe},radius:{value:4}},vertexShader:uA,fragmentShader:dA}),p=f.clone();p.defines.HORIZONTAL_PASS=1;const g=new Cn;g.setAttribute("position",new di(new Float32Array([-1,-1,.5,3,-1,.5,-1,3,.5]),3));const x=new Tn(g,f),m=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=Ev;let u=this.type;this.render=function(C,A,P){if(m.enabled===!1||m.autoUpdate===!1&&m.needsUpdate===!1||C.length===0)return;const E=t.getRenderTarget(),S=t.getActiveCubeFace(),D=t.getActiveMipmapLevel(),X=t.state;X.setBlending(lr),X.buffers.color.setClear(1,1,1,1),X.buffers.depth.setTest(!0),X.setScissorTest(!1);const H=u!==Si&&this.type===Si,U=u===Si&&this.type!==Si;for(let Y=0,V=C.length;Y<V;Y++){const J=C[Y],N=J.shadow;if(N===void 0){console.warn("THREE.WebGLShadowMap:",J,"has no shadow.");continue}if(N.autoUpdate===!1&&N.needsUpdate===!1)continue;r.copy(N.mapSize);const j=N.getFrameExtents();if(r.multiply(j),s.copy(N.mapSize),(r.x>d||r.y>d)&&(r.x>d&&(s.x=Math.floor(d/j.x),r.x=s.x*j.x,N.mapSize.x=s.x),r.y>d&&(s.y=Math.floor(d/j.y),r.y=s.y*j.y,N.mapSize.y=s.y)),N.map===null||H===!0||U===!0){const fe=this.type!==Si?{minFilter:ni,magFilter:ni}:{};N.map!==null&&N.map.dispose(),N.map=new Gr(r.x,r.y,fe),N.map.texture.name=J.name+".shadowMap",N.camera.updateProjectionMatrix()}t.setRenderTarget(N.map),t.clear();const Z=N.getViewportCount();for(let fe=0;fe<Z;fe++){const _e=N.getViewport(fe);o.set(s.x*_e.x,s.y*_e.y,s.x*_e.z,s.y*_e.w),X.viewport(o),N.updateMatrices(J,fe),i=N.getFrustum(),M(A,P,N.camera,J,this.type)}N.isPointLightShadow!==!0&&this.type===Si&&_(N,P),N.needsUpdate=!1}u=this.type,m.needsUpdate=!1,t.setRenderTarget(E,S,D)};function _(C,A){const P=e.update(x);f.defines.VSM_SAMPLES!==C.blurSamples&&(f.defines.VSM_SAMPLES=C.blurSamples,p.defines.VSM_SAMPLES=C.blurSamples,f.needsUpdate=!0,p.needsUpdate=!0),C.mapPass===null&&(C.mapPass=new Gr(r.x,r.y)),f.uniforms.shadow_pass.value=C.map.texture,f.uniforms.resolution.value=C.mapSize,f.uniforms.radius.value=C.radius,t.setRenderTarget(C.mapPass),t.clear(),t.renderBufferDirect(A,null,P,f,x,null),p.uniforms.shadow_pass.value=C.mapPass.texture,p.uniforms.resolution.value=C.mapSize,p.uniforms.radius.value=C.radius,t.setRenderTarget(C.map),t.clear(),t.renderBufferDirect(A,null,P,p,x,null)}function v(C,A,P,E){let S=null;const D=P.isPointLight===!0?C.customDistanceMaterial:C.customDepthMaterial;if(D!==void 0)S=D;else if(S=P.isPointLight===!0?l:a,t.localClippingEnabled&&A.clipShadows===!0&&Array.isArray(A.clippingPlanes)&&A.clippingPlanes.length!==0||A.displacementMap&&A.displacementScale!==0||A.alphaMap&&A.alphaTest>0||A.map&&A.alphaTest>0){const X=S.uuid,H=A.uuid;let U=c[X];U===void 0&&(U={},c[X]=U);let Y=U[H];Y===void 0&&(Y=S.clone(),U[H]=Y,A.addEventListener("dispose",R)),S=Y}if(S.visible=A.visible,S.wireframe=A.wireframe,E===Si?S.side=A.shadowSide!==null?A.shadowSide:A.side:S.side=A.shadowSide!==null?A.shadowSide:h[A.side],S.alphaMap=A.alphaMap,S.alphaTest=A.alphaTest,S.map=A.map,S.clipShadows=A.clipShadows,S.clippingPlanes=A.clippingPlanes,S.clipIntersection=A.clipIntersection,S.displacementMap=A.displacementMap,S.displacementScale=A.displacementScale,S.displacementBias=A.displacementBias,S.wireframeLinewidth=A.wireframeLinewidth,S.linewidth=A.linewidth,P.isPointLight===!0&&S.isMeshDistanceMaterial===!0){const X=t.properties.get(S);X.light=P}return S}function M(C,A,P,E,S){if(C.visible===!1)return;if(C.layers.test(A.layers)&&(C.isMesh||C.isLine||C.isPoints)&&(C.castShadow||C.receiveShadow&&S===Si)&&(!C.frustumCulled||i.intersectsObject(C))){C.modelViewMatrix.multiplyMatrices(P.matrixWorldInverse,C.matrixWorld);const H=e.update(C),U=C.material;if(Array.isArray(U)){const Y=H.groups;for(let V=0,J=Y.length;V<J;V++){const N=Y[V],j=U[N.materialIndex];if(j&&j.visible){const Z=v(C,j,E,S);C.onBeforeShadow(t,C,A,P,H,Z,N),t.renderBufferDirect(P,null,H,Z,C,N),C.onAfterShadow(t,C,A,P,H,Z,N)}}}else if(U.visible){const Y=v(C,U,E,S);C.onBeforeShadow(t,C,A,P,H,Y,null),t.renderBufferDirect(P,null,H,Y,C,null),C.onAfterShadow(t,C,A,P,H,Y,null)}}const X=C.children;for(let H=0,U=X.length;H<U;H++)M(X[H],A,P,E,S)}function R(C){C.target.removeEventListener("dispose",R);for(const P in c){const E=c[P],S=C.target.uuid;S in E&&(E[S].dispose(),delete E[S])}}}const fA={[kd]:Bd,[zd]:Gd,[Hd]:jd,[js]:Vd,[Bd]:kd,[Gd]:zd,[jd]:Hd,[Vd]:js};function pA(t,e){function n(){let F=!1;const xe=new Rt;let q=null;const re=new Rt(0,0,0,0);return{setMask:function(be){q!==be&&!F&&(t.colorMask(be,be,be,be),q=be)},setLocked:function(be){F=be},setClear:function(be,Ae,Ke,xt,Lt){Lt===!0&&(be*=xt,Ae*=xt,Ke*=xt),xe.set(be,Ae,Ke,xt),re.equals(xe)===!1&&(t.clearColor(be,Ae,Ke,xt),re.copy(xe))},reset:function(){F=!1,q=null,re.set(-1,0,0,0)}}}function i(){let F=!1,xe=!1,q=null,re=null,be=null;return{setReversed:function(Ae){if(xe!==Ae){const Ke=e.get("EXT_clip_control");xe?Ke.clipControlEXT(Ke.LOWER_LEFT_EXT,Ke.ZERO_TO_ONE_EXT):Ke.clipControlEXT(Ke.LOWER_LEFT_EXT,Ke.NEGATIVE_ONE_TO_ONE_EXT);const xt=be;be=null,this.setClear(xt)}xe=Ae},getReversed:function(){return xe},setTest:function(Ae){Ae?le(t.DEPTH_TEST):ye(t.DEPTH_TEST)},setMask:function(Ae){q!==Ae&&!F&&(t.depthMask(Ae),q=Ae)},setFunc:function(Ae){if(xe&&(Ae=fA[Ae]),re!==Ae){switch(Ae){case kd:t.depthFunc(t.NEVER);break;case Bd:t.depthFunc(t.ALWAYS);break;case zd:t.depthFunc(t.LESS);break;case js:t.depthFunc(t.LEQUAL);break;case Hd:t.depthFunc(t.EQUAL);break;case Vd:t.depthFunc(t.GEQUAL);break;case Gd:t.depthFunc(t.GREATER);break;case jd:t.depthFunc(t.NOTEQUAL);break;default:t.depthFunc(t.LEQUAL)}re=Ae}},setLocked:function(Ae){F=Ae},setClear:function(Ae){be!==Ae&&(xe&&(Ae=1-Ae),t.clearDepth(Ae),be=Ae)},reset:function(){F=!1,q=null,re=null,be=null,xe=!1}}}function r(){let F=!1,xe=null,q=null,re=null,be=null,Ae=null,Ke=null,xt=null,Lt=null;return{setTest:function(it){F||(it?le(t.STENCIL_TEST):ye(t.STENCIL_TEST))},setMask:function(it){xe!==it&&!F&&(t.stencilMask(it),xe=it)},setFunc:function(it,xn,Vn){(q!==it||re!==xn||be!==Vn)&&(t.stencilFunc(it,xn,Vn),q=it,re=xn,be=Vn)},setOp:function(it,xn,Vn){(Ae!==it||Ke!==xn||xt!==Vn)&&(t.stencilOp(it,xn,Vn),Ae=it,Ke=xn,xt=Vn)},setLocked:function(it){F=it},setClear:function(it){Lt!==it&&(t.clearStencil(it),Lt=it)},reset:function(){F=!1,xe=null,q=null,re=null,be=null,Ae=null,Ke=null,xt=null,Lt=null}}}const s=new n,o=new i,a=new r,l=new WeakMap,c=new WeakMap;let d={},h={},f=new WeakMap,p=[],g=null,x=!1,m=null,u=null,_=null,v=null,M=null,R=null,C=null,A=new ct(0,0,0),P=0,E=!1,S=null,D=null,X=null,H=null,U=null;const Y=t.getParameter(t.MAX_COMBINED_TEXTURE_IMAGE_UNITS);let V=!1,J=0;const N=t.getParameter(t.VERSION);N.indexOf("WebGL")!==-1?(J=parseFloat(/^WebGL (\d)/.exec(N)[1]),V=J>=1):N.indexOf("OpenGL ES")!==-1&&(J=parseFloat(/^OpenGL ES (\d)/.exec(N)[1]),V=J>=2);let j=null,Z={};const fe=t.getParameter(t.SCISSOR_BOX),_e=t.getParameter(t.VIEWPORT),Re=new Rt().fromArray(fe),I=new Rt().fromArray(_e);function z(F,xe,q,re){const be=new Uint8Array(4),Ae=t.createTexture();t.bindTexture(F,Ae),t.texParameteri(F,t.TEXTURE_MIN_FILTER,t.NEAREST),t.texParameteri(F,t.TEXTURE_MAG_FILTER,t.NEAREST);for(let Ke=0;Ke<q;Ke++)F===t.TEXTURE_3D||F===t.TEXTURE_2D_ARRAY?t.texImage3D(xe,0,t.RGBA,1,1,re,0,t.RGBA,t.UNSIGNED_BYTE,be):t.texImage2D(xe+Ke,0,t.RGBA,1,1,0,t.RGBA,t.UNSIGNED_BYTE,be);return Ae}const ie={};ie[t.TEXTURE_2D]=z(t.TEXTURE_2D,t.TEXTURE_2D,1),ie[t.TEXTURE_CUBE_MAP]=z(t.TEXTURE_CUBE_MAP,t.TEXTURE_CUBE_MAP_POSITIVE_X,6),ie[t.TEXTURE_2D_ARRAY]=z(t.TEXTURE_2D_ARRAY,t.TEXTURE_2D_ARRAY,1,1),ie[t.TEXTURE_3D]=z(t.TEXTURE_3D,t.TEXTURE_3D,1,1),s.setClear(0,0,0,1),o.setClear(1),a.setClear(0),le(t.DEPTH_TEST),o.setFunc(js),ze(!1),He(Wp),le(t.CULL_FACE),L(lr);function le(F){d[F]!==!0&&(t.enable(F),d[F]=!0)}function ye(F){d[F]!==!1&&(t.disable(F),d[F]=!1)}function oe(F,xe){return h[F]!==xe?(t.bindFramebuffer(F,xe),h[F]=xe,F===t.DRAW_FRAMEBUFFER&&(h[t.FRAMEBUFFER]=xe),F===t.FRAMEBUFFER&&(h[t.DRAW_FRAMEBUFFER]=xe),!0):!1}function te(F,xe){let q=p,re=!1;if(F){q=f.get(xe),q===void 0&&(q=[],f.set(xe,q));const be=F.textures;if(q.length!==be.length||q[0]!==t.COLOR_ATTACHMENT0){for(let Ae=0,Ke=be.length;Ae<Ke;Ae++)q[Ae]=t.COLOR_ATTACHMENT0+Ae;q.length=be.length,re=!0}}else q[0]!==t.BACK&&(q[0]=t.BACK,re=!0);re&&t.drawBuffers(q)}function me(F){return g!==F?(t.useProgram(F),g=F,!0):!1}const pe={[br]:t.FUNC_ADD,[oS]:t.FUNC_SUBTRACT,[aS]:t.FUNC_REVERSE_SUBTRACT};pe[lS]=t.MIN,pe[cS]=t.MAX;const Ue={[uS]:t.ZERO,[dS]:t.ONE,[hS]:t.SRC_COLOR,[Od]:t.SRC_ALPHA,[vS]:t.SRC_ALPHA_SATURATE,[gS]:t.DST_COLOR,[pS]:t.DST_ALPHA,[fS]:t.ONE_MINUS_SRC_COLOR,[Fd]:t.ONE_MINUS_SRC_ALPHA,[_S]:t.ONE_MINUS_DST_COLOR,[mS]:t.ONE_MINUS_DST_ALPHA,[xS]:t.CONSTANT_COLOR,[yS]:t.ONE_MINUS_CONSTANT_COLOR,[SS]:t.CONSTANT_ALPHA,[MS]:t.ONE_MINUS_CONSTANT_ALPHA};function L(F,xe,q,re,be,Ae,Ke,xt,Lt,it){if(F===lr){x===!0&&(ye(t.BLEND),x=!1);return}if(x===!1&&(le(t.BLEND),x=!0),F!==sS){if(F!==m||it!==E){if((u!==br||M!==br)&&(t.blendEquation(t.FUNC_ADD),u=br,M=br),it)switch(F){case Is:t.blendFuncSeparate(t.ONE,t.ONE_MINUS_SRC_ALPHA,t.ONE,t.ONE_MINUS_SRC_ALPHA);break;case Xp:t.blendFunc(t.ONE,t.ONE);break;case $p:t.blendFuncSeparate(t.ZERO,t.ONE_MINUS_SRC_COLOR,t.ZERO,t.ONE);break;case Yp:t.blendFuncSeparate(t.ZERO,t.SRC_COLOR,t.ZERO,t.SRC_ALPHA);break;default:console.error("THREE.WebGLState: Invalid blending: ",F);break}else switch(F){case Is:t.blendFuncSeparate(t.SRC_ALPHA,t.ONE_MINUS_SRC_ALPHA,t.ONE,t.ONE_MINUS_SRC_ALPHA);break;case Xp:t.blendFunc(t.SRC_ALPHA,t.ONE);break;case $p:t.blendFuncSeparate(t.ZERO,t.ONE_MINUS_SRC_COLOR,t.ZERO,t.ONE);break;case Yp:t.blendFunc(t.ZERO,t.SRC_COLOR);break;default:console.error("THREE.WebGLState: Invalid blending: ",F);break}_=null,v=null,R=null,C=null,A.set(0,0,0),P=0,m=F,E=it}return}be=be||xe,Ae=Ae||q,Ke=Ke||re,(xe!==u||be!==M)&&(t.blendEquationSeparate(pe[xe],pe[be]),u=xe,M=be),(q!==_||re!==v||Ae!==R||Ke!==C)&&(t.blendFuncSeparate(Ue[q],Ue[re],Ue[Ae],Ue[Ke]),_=q,v=re,R=Ae,C=Ke),(xt.equals(A)===!1||Lt!==P)&&(t.blendColor(xt.r,xt.g,xt.b,Lt),A.copy(xt),P=Lt),m=F,E=!1}function Xe(F,xe){F.side===wi?ye(t.CULL_FACE):le(t.CULL_FACE);let q=F.side===gn;xe&&(q=!q),ze(q),F.blending===Is&&F.transparent===!1?L(lr):L(F.blending,F.blendEquation,F.blendSrc,F.blendDst,F.blendEquationAlpha,F.blendSrcAlpha,F.blendDstAlpha,F.blendColor,F.blendAlpha,F.premultipliedAlpha),o.setFunc(F.depthFunc),o.setTest(F.depthTest),o.setMask(F.depthWrite),s.setMask(F.colorWrite);const re=F.stencilWrite;a.setTest(re),re&&(a.setMask(F.stencilWriteMask),a.setFunc(F.stencilFunc,F.stencilRef,F.stencilFuncMask),a.setOp(F.stencilFail,F.stencilZFail,F.stencilZPass)),$e(F.polygonOffset,F.polygonOffsetFactor,F.polygonOffsetUnits),F.alphaToCoverage===!0?le(t.SAMPLE_ALPHA_TO_COVERAGE):ye(t.SAMPLE_ALPHA_TO_COVERAGE)}function ze(F){S!==F&&(F?t.frontFace(t.CW):t.frontFace(t.CCW),S=F)}function He(F){F!==nS?(le(t.CULL_FACE),F!==D&&(F===Wp?t.cullFace(t.BACK):F===iS?t.cullFace(t.FRONT):t.cullFace(t.FRONT_AND_BACK))):ye(t.CULL_FACE),D=F}function Te(F){F!==X&&(V&&t.lineWidth(F),X=F)}function $e(F,xe,q){F?(le(t.POLYGON_OFFSET_FILL),(H!==xe||U!==q)&&(t.polygonOffset(xe,q),H=xe,U=q)):ye(t.POLYGON_OFFSET_FILL)}function we(F){F?le(t.SCISSOR_TEST):ye(t.SCISSOR_TEST)}function b(F){F===void 0&&(F=t.TEXTURE0+Y-1),j!==F&&(t.activeTexture(F),j=F)}function w(F,xe,q){q===void 0&&(j===null?q=t.TEXTURE0+Y-1:q=j);let re=Z[q];re===void 0&&(re={type:void 0,texture:void 0},Z[q]=re),(re.type!==F||re.texture!==xe)&&(j!==q&&(t.activeTexture(q),j=q),t.bindTexture(F,xe||ie[F]),re.type=F,re.texture=xe)}function G(){const F=Z[j];F!==void 0&&F.type!==void 0&&(t.bindTexture(F.type,null),F.type=void 0,F.texture=void 0)}function ne(){try{t.compressedTexImage2D.apply(t,arguments)}catch(F){console.error("THREE.WebGLState:",F)}}function ae(){try{t.compressedTexImage3D.apply(t,arguments)}catch(F){console.error("THREE.WebGLState:",F)}}function ee(){try{t.texSubImage2D.apply(t,arguments)}catch(F){console.error("THREE.WebGLState:",F)}}function Ie(){try{t.texSubImage3D.apply(t,arguments)}catch(F){console.error("THREE.WebGLState:",F)}}function Se(){try{t.compressedTexSubImage2D.apply(t,arguments)}catch(F){console.error("THREE.WebGLState:",F)}}function Pe(){try{t.compressedTexSubImage3D.apply(t,arguments)}catch(F){console.error("THREE.WebGLState:",F)}}function tt(){try{t.texStorage2D.apply(t,arguments)}catch(F){console.error("THREE.WebGLState:",F)}}function K(){try{t.texStorage3D.apply(t,arguments)}catch(F){console.error("THREE.WebGLState:",F)}}function se(){try{t.texImage2D.apply(t,arguments)}catch(F){console.error("THREE.WebGLState:",F)}}function ve(){try{t.texImage3D.apply(t,arguments)}catch(F){console.error("THREE.WebGLState:",F)}}function Me(F){Re.equals(F)===!1&&(t.scissor(F.x,F.y,F.z,F.w),Re.copy(F))}function ue(F){I.equals(F)===!1&&(t.viewport(F.x,F.y,F.z,F.w),I.copy(F))}function je(F,xe){let q=c.get(xe);q===void 0&&(q=new WeakMap,c.set(xe,q));let re=q.get(F);re===void 0&&(re=t.getUniformBlockIndex(xe,F.name),q.set(F,re))}function Ve(F,xe){const re=c.get(xe).get(F);l.get(xe)!==re&&(t.uniformBlockBinding(xe,re,F.__bindingPointIndex),l.set(xe,re))}function Qe(){t.disable(t.BLEND),t.disable(t.CULL_FACE),t.disable(t.DEPTH_TEST),t.disable(t.POLYGON_OFFSET_FILL),t.disable(t.SCISSOR_TEST),t.disable(t.STENCIL_TEST),t.disable(t.SAMPLE_ALPHA_TO_COVERAGE),t.blendEquation(t.FUNC_ADD),t.blendFunc(t.ONE,t.ZERO),t.blendFuncSeparate(t.ONE,t.ZERO,t.ONE,t.ZERO),t.blendColor(0,0,0,0),t.colorMask(!0,!0,!0,!0),t.clearColor(0,0,0,0),t.depthMask(!0),t.depthFunc(t.LESS),o.setReversed(!1),t.clearDepth(1),t.stencilMask(4294967295),t.stencilFunc(t.ALWAYS,0,4294967295),t.stencilOp(t.KEEP,t.KEEP,t.KEEP),t.clearStencil(0),t.cullFace(t.BACK),t.frontFace(t.CCW),t.polygonOffset(0,0),t.activeTexture(t.TEXTURE0),t.bindFramebuffer(t.FRAMEBUFFER,null),t.bindFramebuffer(t.DRAW_FRAMEBUFFER,null),t.bindFramebuffer(t.READ_FRAMEBUFFER,null),t.useProgram(null),t.lineWidth(1),t.scissor(0,0,t.canvas.width,t.canvas.height),t.viewport(0,0,t.canvas.width,t.canvas.height),d={},j=null,Z={},h={},f=new WeakMap,p=[],g=null,x=!1,m=null,u=null,_=null,v=null,M=null,R=null,C=null,A=new ct(0,0,0),P=0,E=!1,S=null,D=null,X=null,H=null,U=null,Re.set(0,0,t.canvas.width,t.canvas.height),I.set(0,0,t.canvas.width,t.canvas.height),s.reset(),o.reset(),a.reset()}return{buffers:{color:s,depth:o,stencil:a},enable:le,disable:ye,bindFramebuffer:oe,drawBuffers:te,useProgram:me,setBlending:L,setMaterial:Xe,setFlipSided:ze,setCullFace:He,setLineWidth:Te,setPolygonOffset:$e,setScissorTest:we,activeTexture:b,bindTexture:w,unbindTexture:G,compressedTexImage2D:ne,compressedTexImage3D:ae,texImage2D:se,texImage3D:ve,updateUBOMapping:je,uniformBlockBinding:Ve,texStorage2D:tt,texStorage3D:K,texSubImage2D:ee,texSubImage3D:Ie,compressedTexSubImage2D:Se,compressedTexSubImage3D:Pe,scissor:Me,viewport:ue,reset:Qe}}function mA(t,e,n,i,r,s,o){const a=e.has("WEBGL_multisampled_render_to_texture")?e.get("WEBGL_multisampled_render_to_texture"):null,l=typeof navigator>"u"?!1:/OculusBrowser/g.test(navigator.userAgent),c=new Fe,d=new WeakMap;let h;const f=new WeakMap;let p=!1;try{p=typeof OffscreenCanvas<"u"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch{}function g(b,w){return p?new OffscreenCanvas(b,w):Jl("canvas")}function x(b,w,G){let ne=1;const ae=we(b);if((ae.width>G||ae.height>G)&&(ne=G/Math.max(ae.width,ae.height)),ne<1)if(typeof HTMLImageElement<"u"&&b instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&b instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&b instanceof ImageBitmap||typeof VideoFrame<"u"&&b instanceof VideoFrame){const ee=Math.floor(ne*ae.width),Ie=Math.floor(ne*ae.height);h===void 0&&(h=g(ee,Ie));const Se=w?g(ee,Ie):h;return Se.width=ee,Se.height=Ie,Se.getContext("2d").drawImage(b,0,0,ee,Ie),console.warn("THREE.WebGLRenderer: Texture has been resized from ("+ae.width+"x"+ae.height+") to ("+ee+"x"+Ie+")."),Se}else return"data"in b&&console.warn("THREE.WebGLRenderer: Image in DataTexture is too big ("+ae.width+"x"+ae.height+")."),b;return b}function m(b){return b.generateMipmaps}function u(b){t.generateMipmap(b)}function _(b){return b.isWebGLCubeRenderTarget?t.TEXTURE_CUBE_MAP:b.isWebGL3DRenderTarget?t.TEXTURE_3D:b.isWebGLArrayRenderTarget||b.isCompressedArrayTexture?t.TEXTURE_2D_ARRAY:t.TEXTURE_2D}function v(b,w,G,ne,ae=!1){if(b!==null){if(t[b]!==void 0)return t[b];console.warn("THREE.WebGLRenderer: Attempt to use non-existing WebGL internal format '"+b+"'")}let ee=w;if(w===t.RED&&(G===t.FLOAT&&(ee=t.R32F),G===t.HALF_FLOAT&&(ee=t.R16F),G===t.UNSIGNED_BYTE&&(ee=t.R8)),w===t.RED_INTEGER&&(G===t.UNSIGNED_BYTE&&(ee=t.R8UI),G===t.UNSIGNED_SHORT&&(ee=t.R16UI),G===t.UNSIGNED_INT&&(ee=t.R32UI),G===t.BYTE&&(ee=t.R8I),G===t.SHORT&&(ee=t.R16I),G===t.INT&&(ee=t.R32I)),w===t.RG&&(G===t.FLOAT&&(ee=t.RG32F),G===t.HALF_FLOAT&&(ee=t.RG16F),G===t.UNSIGNED_BYTE&&(ee=t.RG8)),w===t.RG_INTEGER&&(G===t.UNSIGNED_BYTE&&(ee=t.RG8UI),G===t.UNSIGNED_SHORT&&(ee=t.RG16UI),G===t.UNSIGNED_INT&&(ee=t.RG32UI),G===t.BYTE&&(ee=t.RG8I),G===t.SHORT&&(ee=t.RG16I),G===t.INT&&(ee=t.RG32I)),w===t.RGB_INTEGER&&(G===t.UNSIGNED_BYTE&&(ee=t.RGB8UI),G===t.UNSIGNED_SHORT&&(ee=t.RGB16UI),G===t.UNSIGNED_INT&&(ee=t.RGB32UI),G===t.BYTE&&(ee=t.RGB8I),G===t.SHORT&&(ee=t.RGB16I),G===t.INT&&(ee=t.RGB32I)),w===t.RGBA_INTEGER&&(G===t.UNSIGNED_BYTE&&(ee=t.RGBA8UI),G===t.UNSIGNED_SHORT&&(ee=t.RGBA16UI),G===t.UNSIGNED_INT&&(ee=t.RGBA32UI),G===t.BYTE&&(ee=t.RGBA8I),G===t.SHORT&&(ee=t.RGBA16I),G===t.INT&&(ee=t.RGBA32I)),w===t.RGB&&G===t.UNSIGNED_INT_5_9_9_9_REV&&(ee=t.RGB9_E5),w===t.RGBA){const Ie=ae?Kl:lt.getTransfer(ne);G===t.FLOAT&&(ee=t.RGBA32F),G===t.HALF_FLOAT&&(ee=t.RGBA16F),G===t.UNSIGNED_BYTE&&(ee=Ie===ft?t.SRGB8_ALPHA8:t.RGBA8),G===t.UNSIGNED_SHORT_4_4_4_4&&(ee=t.RGBA4),G===t.UNSIGNED_SHORT_5_5_5_1&&(ee=t.RGB5_A1)}return(ee===t.R16F||ee===t.R32F||ee===t.RG16F||ee===t.RG32F||ee===t.RGBA16F||ee===t.RGBA32F)&&e.get("EXT_color_buffer_float"),ee}function M(b,w){let G;return b?w===null||w===Vr||w===$s?G=t.DEPTH24_STENCIL8:w===Ci?G=t.DEPTH32F_STENCIL8:w===ea&&(G=t.DEPTH24_STENCIL8,console.warn("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")):w===null||w===Vr||w===$s?G=t.DEPTH_COMPONENT24:w===Ci?G=t.DEPTH_COMPONENT32F:w===ea&&(G=t.DEPTH_COMPONENT16),G}function R(b,w){return m(b)===!0||b.isFramebufferTexture&&b.minFilter!==ni&&b.minFilter!==li?Math.log2(Math.max(w.width,w.height))+1:b.mipmaps!==void 0&&b.mipmaps.length>0?b.mipmaps.length:b.isCompressedTexture&&Array.isArray(b.image)?w.mipmaps.length:1}function C(b){const w=b.target;w.removeEventListener("dispose",C),P(w),w.isVideoTexture&&d.delete(w)}function A(b){const w=b.target;w.removeEventListener("dispose",A),S(w)}function P(b){const w=i.get(b);if(w.__webglInit===void 0)return;const G=b.source,ne=f.get(G);if(ne){const ae=ne[w.__cacheKey];ae.usedTimes--,ae.usedTimes===0&&E(b),Object.keys(ne).length===0&&f.delete(G)}i.remove(b)}function E(b){const w=i.get(b);t.deleteTexture(w.__webglTexture);const G=b.source,ne=f.get(G);delete ne[w.__cacheKey],o.memory.textures--}function S(b){const w=i.get(b);if(b.depthTexture&&(b.depthTexture.dispose(),i.remove(b.depthTexture)),b.isWebGLCubeRenderTarget)for(let ne=0;ne<6;ne++){if(Array.isArray(w.__webglFramebuffer[ne]))for(let ae=0;ae<w.__webglFramebuffer[ne].length;ae++)t.deleteFramebuffer(w.__webglFramebuffer[ne][ae]);else t.deleteFramebuffer(w.__webglFramebuffer[ne]);w.__webglDepthbuffer&&t.deleteRenderbuffer(w.__webglDepthbuffer[ne])}else{if(Array.isArray(w.__webglFramebuffer))for(let ne=0;ne<w.__webglFramebuffer.length;ne++)t.deleteFramebuffer(w.__webglFramebuffer[ne]);else t.deleteFramebuffer(w.__webglFramebuffer);if(w.__webglDepthbuffer&&t.deleteRenderbuffer(w.__webglDepthbuffer),w.__webglMultisampledFramebuffer&&t.deleteFramebuffer(w.__webglMultisampledFramebuffer),w.__webglColorRenderbuffer)for(let ne=0;ne<w.__webglColorRenderbuffer.length;ne++)w.__webglColorRenderbuffer[ne]&&t.deleteRenderbuffer(w.__webglColorRenderbuffer[ne]);w.__webglDepthRenderbuffer&&t.deleteRenderbuffer(w.__webglDepthRenderbuffer)}const G=b.textures;for(let ne=0,ae=G.length;ne<ae;ne++){const ee=i.get(G[ne]);ee.__webglTexture&&(t.deleteTexture(ee.__webglTexture),o.memory.textures--),i.remove(G[ne])}i.remove(b)}let D=0;function X(){D=0}function H(){const b=D;return b>=r.maxTextures&&console.warn("THREE.WebGLTextures: Trying to use "+b+" texture units while this GPU supports only "+r.maxTextures),D+=1,b}function U(b){const w=[];return w.push(b.wrapS),w.push(b.wrapT),w.push(b.wrapR||0),w.push(b.magFilter),w.push(b.minFilter),w.push(b.anisotropy),w.push(b.internalFormat),w.push(b.format),w.push(b.type),w.push(b.generateMipmaps),w.push(b.premultiplyAlpha),w.push(b.flipY),w.push(b.unpackAlignment),w.push(b.colorSpace),w.join()}function Y(b,w){const G=i.get(b);if(b.isVideoTexture&&Te(b),b.isRenderTargetTexture===!1&&b.version>0&&G.__version!==b.version){const ne=b.image;if(ne===null)console.warn("THREE.WebGLRenderer: Texture marked for update but no image data found.");else if(ne.complete===!1)console.warn("THREE.WebGLRenderer: Texture marked for update but image is incomplete");else{I(G,b,w);return}}n.bindTexture(t.TEXTURE_2D,G.__webglTexture,t.TEXTURE0+w)}function V(b,w){const G=i.get(b);if(b.version>0&&G.__version!==b.version){I(G,b,w);return}n.bindTexture(t.TEXTURE_2D_ARRAY,G.__webglTexture,t.TEXTURE0+w)}function J(b,w){const G=i.get(b);if(b.version>0&&G.__version!==b.version){I(G,b,w);return}n.bindTexture(t.TEXTURE_3D,G.__webglTexture,t.TEXTURE0+w)}function N(b,w){const G=i.get(b);if(b.version>0&&G.__version!==b.version){z(G,b,w);return}n.bindTexture(t.TEXTURE_CUBE_MAP,G.__webglTexture,t.TEXTURE0+w)}const j={[$d]:t.REPEAT,[Dr]:t.CLAMP_TO_EDGE,[Yd]:t.MIRRORED_REPEAT},Z={[ni]:t.NEAREST,[NS]:t.NEAREST_MIPMAP_NEAREST,[La]:t.NEAREST_MIPMAP_LINEAR,[li]:t.LINEAR,[nu]:t.LINEAR_MIPMAP_NEAREST,[Ir]:t.LINEAR_MIPMAP_LINEAR},fe={[OS]:t.NEVER,[VS]:t.ALWAYS,[FS]:t.LESS,[Fv]:t.LEQUAL,[kS]:t.EQUAL,[HS]:t.GEQUAL,[BS]:t.GREATER,[zS]:t.NOTEQUAL};function _e(b,w){if(w.type===Ci&&e.has("OES_texture_float_linear")===!1&&(w.magFilter===li||w.magFilter===nu||w.magFilter===La||w.magFilter===Ir||w.minFilter===li||w.minFilter===nu||w.minFilter===La||w.minFilter===Ir)&&console.warn("THREE.WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device."),t.texParameteri(b,t.TEXTURE_WRAP_S,j[w.wrapS]),t.texParameteri(b,t.TEXTURE_WRAP_T,j[w.wrapT]),(b===t.TEXTURE_3D||b===t.TEXTURE_2D_ARRAY)&&t.texParameteri(b,t.TEXTURE_WRAP_R,j[w.wrapR]),t.texParameteri(b,t.TEXTURE_MAG_FILTER,Z[w.magFilter]),t.texParameteri(b,t.TEXTURE_MIN_FILTER,Z[w.minFilter]),w.compareFunction&&(t.texParameteri(b,t.TEXTURE_COMPARE_MODE,t.COMPARE_REF_TO_TEXTURE),t.texParameteri(b,t.TEXTURE_COMPARE_FUNC,fe[w.compareFunction])),e.has("EXT_texture_filter_anisotropic")===!0){if(w.magFilter===ni||w.minFilter!==La&&w.minFilter!==Ir||w.type===Ci&&e.has("OES_texture_float_linear")===!1)return;if(w.anisotropy>1||i.get(w).__currentAnisotropy){const G=e.get("EXT_texture_filter_anisotropic");t.texParameterf(b,G.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(w.anisotropy,r.getMaxAnisotropy())),i.get(w).__currentAnisotropy=w.anisotropy}}}function Re(b,w){let G=!1;b.__webglInit===void 0&&(b.__webglInit=!0,w.addEventListener("dispose",C));const ne=w.source;let ae=f.get(ne);ae===void 0&&(ae={},f.set(ne,ae));const ee=U(w);if(ee!==b.__cacheKey){ae[ee]===void 0&&(ae[ee]={texture:t.createTexture(),usedTimes:0},o.memory.textures++,G=!0),ae[ee].usedTimes++;const Ie=ae[b.__cacheKey];Ie!==void 0&&(ae[b.__cacheKey].usedTimes--,Ie.usedTimes===0&&E(w)),b.__cacheKey=ee,b.__webglTexture=ae[ee].texture}return G}function I(b,w,G){let ne=t.TEXTURE_2D;(w.isDataArrayTexture||w.isCompressedArrayTexture)&&(ne=t.TEXTURE_2D_ARRAY),w.isData3DTexture&&(ne=t.TEXTURE_3D);const ae=Re(b,w),ee=w.source;n.bindTexture(ne,b.__webglTexture,t.TEXTURE0+G);const Ie=i.get(ee);if(ee.version!==Ie.__version||ae===!0){n.activeTexture(t.TEXTURE0+G);const Se=lt.getPrimaries(lt.workingColorSpace),Pe=w.colorSpace===Zi?null:lt.getPrimaries(w.colorSpace),tt=w.colorSpace===Zi||Se===Pe?t.NONE:t.BROWSER_DEFAULT_WEBGL;t.pixelStorei(t.UNPACK_FLIP_Y_WEBGL,w.flipY),t.pixelStorei(t.UNPACK_PREMULTIPLY_ALPHA_WEBGL,w.premultiplyAlpha),t.pixelStorei(t.UNPACK_ALIGNMENT,w.unpackAlignment),t.pixelStorei(t.UNPACK_COLORSPACE_CONVERSION_WEBGL,tt);let K=x(w.image,!1,r.maxTextureSize);K=$e(w,K);const se=s.convert(w.format,w.colorSpace),ve=s.convert(w.type);let Me=v(w.internalFormat,se,ve,w.colorSpace,w.isVideoTexture);_e(ne,w);let ue;const je=w.mipmaps,Ve=w.isVideoTexture!==!0,Qe=Ie.__version===void 0||ae===!0,F=ee.dataReady,xe=R(w,K);if(w.isDepthTexture)Me=M(w.format===Ys,w.type),Qe&&(Ve?n.texStorage2D(t.TEXTURE_2D,1,Me,K.width,K.height):n.texImage2D(t.TEXTURE_2D,0,Me,K.width,K.height,0,se,ve,null));else if(w.isDataTexture)if(je.length>0){Ve&&Qe&&n.texStorage2D(t.TEXTURE_2D,xe,Me,je[0].width,je[0].height);for(let q=0,re=je.length;q<re;q++)ue=je[q],Ve?F&&n.texSubImage2D(t.TEXTURE_2D,q,0,0,ue.width,ue.height,se,ve,ue.data):n.texImage2D(t.TEXTURE_2D,q,Me,ue.width,ue.height,0,se,ve,ue.data);w.generateMipmaps=!1}else Ve?(Qe&&n.texStorage2D(t.TEXTURE_2D,xe,Me,K.width,K.height),F&&n.texSubImage2D(t.TEXTURE_2D,0,0,0,K.width,K.height,se,ve,K.data)):n.texImage2D(t.TEXTURE_2D,0,Me,K.width,K.height,0,se,ve,K.data);else if(w.isCompressedTexture)if(w.isCompressedArrayTexture){Ve&&Qe&&n.texStorage3D(t.TEXTURE_2D_ARRAY,xe,Me,je[0].width,je[0].height,K.depth);for(let q=0,re=je.length;q<re;q++)if(ue=je[q],w.format!==Qn)if(se!==null)if(Ve){if(F)if(w.layerUpdates.size>0){const be=wm(ue.width,ue.height,w.format,w.type);for(const Ae of w.layerUpdates){const Ke=ue.data.subarray(Ae*be/ue.data.BYTES_PER_ELEMENT,(Ae+1)*be/ue.data.BYTES_PER_ELEMENT);n.compressedTexSubImage3D(t.TEXTURE_2D_ARRAY,q,0,0,Ae,ue.width,ue.height,1,se,Ke)}w.clearLayerUpdates()}else n.compressedTexSubImage3D(t.TEXTURE_2D_ARRAY,q,0,0,0,ue.width,ue.height,K.depth,se,ue.data)}else n.compressedTexImage3D(t.TEXTURE_2D_ARRAY,q,Me,ue.width,ue.height,K.depth,0,ue.data,0,0);else console.warn("THREE.WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else Ve?F&&n.texSubImage3D(t.TEXTURE_2D_ARRAY,q,0,0,0,ue.width,ue.height,K.depth,se,ve,ue.data):n.texImage3D(t.TEXTURE_2D_ARRAY,q,Me,ue.width,ue.height,K.depth,0,se,ve,ue.data)}else{Ve&&Qe&&n.texStorage2D(t.TEXTURE_2D,xe,Me,je[0].width,je[0].height);for(let q=0,re=je.length;q<re;q++)ue=je[q],w.format!==Qn?se!==null?Ve?F&&n.compressedTexSubImage2D(t.TEXTURE_2D,q,0,0,ue.width,ue.height,se,ue.data):n.compressedTexImage2D(t.TEXTURE_2D,q,Me,ue.width,ue.height,0,ue.data):console.warn("THREE.WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()"):Ve?F&&n.texSubImage2D(t.TEXTURE_2D,q,0,0,ue.width,ue.height,se,ve,ue.data):n.texImage2D(t.TEXTURE_2D,q,Me,ue.width,ue.height,0,se,ve,ue.data)}else if(w.isDataArrayTexture)if(Ve){if(Qe&&n.texStorage3D(t.TEXTURE_2D_ARRAY,xe,Me,K.width,K.height,K.depth),F)if(w.layerUpdates.size>0){const q=wm(K.width,K.height,w.format,w.type);for(const re of w.layerUpdates){const be=K.data.subarray(re*q/K.data.BYTES_PER_ELEMENT,(re+1)*q/K.data.BYTES_PER_ELEMENT);n.texSubImage3D(t.TEXTURE_2D_ARRAY,0,0,0,re,K.width,K.height,1,se,ve,be)}w.clearLayerUpdates()}else n.texSubImage3D(t.TEXTURE_2D_ARRAY,0,0,0,0,K.width,K.height,K.depth,se,ve,K.data)}else n.texImage3D(t.TEXTURE_2D_ARRAY,0,Me,K.width,K.height,K.depth,0,se,ve,K.data);else if(w.isData3DTexture)Ve?(Qe&&n.texStorage3D(t.TEXTURE_3D,xe,Me,K.width,K.height,K.depth),F&&n.texSubImage3D(t.TEXTURE_3D,0,0,0,0,K.width,K.height,K.depth,se,ve,K.data)):n.texImage3D(t.TEXTURE_3D,0,Me,K.width,K.height,K.depth,0,se,ve,K.data);else if(w.isFramebufferTexture){if(Qe)if(Ve)n.texStorage2D(t.TEXTURE_2D,xe,Me,K.width,K.height);else{let q=K.width,re=K.height;for(let be=0;be<xe;be++)n.texImage2D(t.TEXTURE_2D,be,Me,q,re,0,se,ve,null),q>>=1,re>>=1}}else if(je.length>0){if(Ve&&Qe){const q=we(je[0]);n.texStorage2D(t.TEXTURE_2D,xe,Me,q.width,q.height)}for(let q=0,re=je.length;q<re;q++)ue=je[q],Ve?F&&n.texSubImage2D(t.TEXTURE_2D,q,0,0,se,ve,ue):n.texImage2D(t.TEXTURE_2D,q,Me,se,ve,ue);w.generateMipmaps=!1}else if(Ve){if(Qe){const q=we(K);n.texStorage2D(t.TEXTURE_2D,xe,Me,q.width,q.height)}F&&n.texSubImage2D(t.TEXTURE_2D,0,0,0,se,ve,K)}else n.texImage2D(t.TEXTURE_2D,0,Me,se,ve,K);m(w)&&u(ne),Ie.__version=ee.version,w.onUpdate&&w.onUpdate(w)}b.__version=w.version}function z(b,w,G){if(w.image.length!==6)return;const ne=Re(b,w),ae=w.source;n.bindTexture(t.TEXTURE_CUBE_MAP,b.__webglTexture,t.TEXTURE0+G);const ee=i.get(ae);if(ae.version!==ee.__version||ne===!0){n.activeTexture(t.TEXTURE0+G);const Ie=lt.getPrimaries(lt.workingColorSpace),Se=w.colorSpace===Zi?null:lt.getPrimaries(w.colorSpace),Pe=w.colorSpace===Zi||Ie===Se?t.NONE:t.BROWSER_DEFAULT_WEBGL;t.pixelStorei(t.UNPACK_FLIP_Y_WEBGL,w.flipY),t.pixelStorei(t.UNPACK_PREMULTIPLY_ALPHA_WEBGL,w.premultiplyAlpha),t.pixelStorei(t.UNPACK_ALIGNMENT,w.unpackAlignment),t.pixelStorei(t.UNPACK_COLORSPACE_CONVERSION_WEBGL,Pe);const tt=w.isCompressedTexture||w.image[0].isCompressedTexture,K=w.image[0]&&w.image[0].isDataTexture,se=[];for(let re=0;re<6;re++)!tt&&!K?se[re]=x(w.image[re],!0,r.maxCubemapSize):se[re]=K?w.image[re].image:w.image[re],se[re]=$e(w,se[re]);const ve=se[0],Me=s.convert(w.format,w.colorSpace),ue=s.convert(w.type),je=v(w.internalFormat,Me,ue,w.colorSpace),Ve=w.isVideoTexture!==!0,Qe=ee.__version===void 0||ne===!0,F=ae.dataReady;let xe=R(w,ve);_e(t.TEXTURE_CUBE_MAP,w);let q;if(tt){Ve&&Qe&&n.texStorage2D(t.TEXTURE_CUBE_MAP,xe,je,ve.width,ve.height);for(let re=0;re<6;re++){q=se[re].mipmaps;for(let be=0;be<q.length;be++){const Ae=q[be];w.format!==Qn?Me!==null?Ve?F&&n.compressedTexSubImage2D(t.TEXTURE_CUBE_MAP_POSITIVE_X+re,be,0,0,Ae.width,Ae.height,Me,Ae.data):n.compressedTexImage2D(t.TEXTURE_CUBE_MAP_POSITIVE_X+re,be,je,Ae.width,Ae.height,0,Ae.data):console.warn("THREE.WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()"):Ve?F&&n.texSubImage2D(t.TEXTURE_CUBE_MAP_POSITIVE_X+re,be,0,0,Ae.width,Ae.height,Me,ue,Ae.data):n.texImage2D(t.TEXTURE_CUBE_MAP_POSITIVE_X+re,be,je,Ae.width,Ae.height,0,Me,ue,Ae.data)}}}else{if(q=w.mipmaps,Ve&&Qe){q.length>0&&xe++;const re=we(se[0]);n.texStorage2D(t.TEXTURE_CUBE_MAP,xe,je,re.width,re.height)}for(let re=0;re<6;re++)if(K){Ve?F&&n.texSubImage2D(t.TEXTURE_CUBE_MAP_POSITIVE_X+re,0,0,0,se[re].width,se[re].height,Me,ue,se[re].data):n.texImage2D(t.TEXTURE_CUBE_MAP_POSITIVE_X+re,0,je,se[re].width,se[re].height,0,Me,ue,se[re].data);for(let be=0;be<q.length;be++){const Ke=q[be].image[re].image;Ve?F&&n.texSubImage2D(t.TEXTURE_CUBE_MAP_POSITIVE_X+re,be+1,0,0,Ke.width,Ke.height,Me,ue,Ke.data):n.texImage2D(t.TEXTURE_CUBE_MAP_POSITIVE_X+re,be+1,je,Ke.width,Ke.height,0,Me,ue,Ke.data)}}else{Ve?F&&n.texSubImage2D(t.TEXTURE_CUBE_MAP_POSITIVE_X+re,0,0,0,Me,ue,se[re]):n.texImage2D(t.TEXTURE_CUBE_MAP_POSITIVE_X+re,0,je,Me,ue,se[re]);for(let be=0;be<q.length;be++){const Ae=q[be];Ve?F&&n.texSubImage2D(t.TEXTURE_CUBE_MAP_POSITIVE_X+re,be+1,0,0,Me,ue,Ae.image[re]):n.texImage2D(t.TEXTURE_CUBE_MAP_POSITIVE_X+re,be+1,je,Me,ue,Ae.image[re])}}}m(w)&&u(t.TEXTURE_CUBE_MAP),ee.__version=ae.version,w.onUpdate&&w.onUpdate(w)}b.__version=w.version}function ie(b,w,G,ne,ae,ee){const Ie=s.convert(G.format,G.colorSpace),Se=s.convert(G.type),Pe=v(G.internalFormat,Ie,Se,G.colorSpace),tt=i.get(w),K=i.get(G);if(K.__renderTarget=w,!tt.__hasExternalTextures){const se=Math.max(1,w.width>>ee),ve=Math.max(1,w.height>>ee);ae===t.TEXTURE_3D||ae===t.TEXTURE_2D_ARRAY?n.texImage3D(ae,ee,Pe,se,ve,w.depth,0,Ie,Se,null):n.texImage2D(ae,ee,Pe,se,ve,0,Ie,Se,null)}n.bindFramebuffer(t.FRAMEBUFFER,b),He(w)?a.framebufferTexture2DMultisampleEXT(t.FRAMEBUFFER,ne,ae,K.__webglTexture,0,ze(w)):(ae===t.TEXTURE_2D||ae>=t.TEXTURE_CUBE_MAP_POSITIVE_X&&ae<=t.TEXTURE_CUBE_MAP_NEGATIVE_Z)&&t.framebufferTexture2D(t.FRAMEBUFFER,ne,ae,K.__webglTexture,ee),n.bindFramebuffer(t.FRAMEBUFFER,null)}function le(b,w,G){if(t.bindRenderbuffer(t.RENDERBUFFER,b),w.depthBuffer){const ne=w.depthTexture,ae=ne&&ne.isDepthTexture?ne.type:null,ee=M(w.stencilBuffer,ae),Ie=w.stencilBuffer?t.DEPTH_STENCIL_ATTACHMENT:t.DEPTH_ATTACHMENT,Se=ze(w);He(w)?a.renderbufferStorageMultisampleEXT(t.RENDERBUFFER,Se,ee,w.width,w.height):G?t.renderbufferStorageMultisample(t.RENDERBUFFER,Se,ee,w.width,w.height):t.renderbufferStorage(t.RENDERBUFFER,ee,w.width,w.height),t.framebufferRenderbuffer(t.FRAMEBUFFER,Ie,t.RENDERBUFFER,b)}else{const ne=w.textures;for(let ae=0;ae<ne.length;ae++){const ee=ne[ae],Ie=s.convert(ee.format,ee.colorSpace),Se=s.convert(ee.type),Pe=v(ee.internalFormat,Ie,Se,ee.colorSpace),tt=ze(w);G&&He(w)===!1?t.renderbufferStorageMultisample(t.RENDERBUFFER,tt,Pe,w.width,w.height):He(w)?a.renderbufferStorageMultisampleEXT(t.RENDERBUFFER,tt,Pe,w.width,w.height):t.renderbufferStorage(t.RENDERBUFFER,Pe,w.width,w.height)}}t.bindRenderbuffer(t.RENDERBUFFER,null)}function ye(b,w){if(w&&w.isWebGLCubeRenderTarget)throw new Error("Depth Texture with cube render targets is not supported");if(n.bindFramebuffer(t.FRAMEBUFFER,b),!(w.depthTexture&&w.depthTexture.isDepthTexture))throw new Error("renderTarget.depthTexture must be an instance of THREE.DepthTexture");const ne=i.get(w.depthTexture);ne.__renderTarget=w,(!ne.__webglTexture||w.depthTexture.image.width!==w.width||w.depthTexture.image.height!==w.height)&&(w.depthTexture.image.width=w.width,w.depthTexture.image.height=w.height,w.depthTexture.needsUpdate=!0),Y(w.depthTexture,0);const ae=ne.__webglTexture,ee=ze(w);if(w.depthTexture.format===Us)He(w)?a.framebufferTexture2DMultisampleEXT(t.FRAMEBUFFER,t.DEPTH_ATTACHMENT,t.TEXTURE_2D,ae,0,ee):t.framebufferTexture2D(t.FRAMEBUFFER,t.DEPTH_ATTACHMENT,t.TEXTURE_2D,ae,0);else if(w.depthTexture.format===Ys)He(w)?a.framebufferTexture2DMultisampleEXT(t.FRAMEBUFFER,t.DEPTH_STENCIL_ATTACHMENT,t.TEXTURE_2D,ae,0,ee):t.framebufferTexture2D(t.FRAMEBUFFER,t.DEPTH_STENCIL_ATTACHMENT,t.TEXTURE_2D,ae,0);else throw new Error("Unknown depthTexture format")}function oe(b){const w=i.get(b),G=b.isWebGLCubeRenderTarget===!0;if(w.__boundDepthTexture!==b.depthTexture){const ne=b.depthTexture;if(w.__depthDisposeCallback&&w.__depthDisposeCallback(),ne){const ae=()=>{delete w.__boundDepthTexture,delete w.__depthDisposeCallback,ne.removeEventListener("dispose",ae)};ne.addEventListener("dispose",ae),w.__depthDisposeCallback=ae}w.__boundDepthTexture=ne}if(b.depthTexture&&!w.__autoAllocateDepthBuffer){if(G)throw new Error("target.depthTexture not supported in Cube render targets");ye(w.__webglFramebuffer,b)}else if(G){w.__webglDepthbuffer=[];for(let ne=0;ne<6;ne++)if(n.bindFramebuffer(t.FRAMEBUFFER,w.__webglFramebuffer[ne]),w.__webglDepthbuffer[ne]===void 0)w.__webglDepthbuffer[ne]=t.createRenderbuffer(),le(w.__webglDepthbuffer[ne],b,!1);else{const ae=b.stencilBuffer?t.DEPTH_STENCIL_ATTACHMENT:t.DEPTH_ATTACHMENT,ee=w.__webglDepthbuffer[ne];t.bindRenderbuffer(t.RENDERBUFFER,ee),t.framebufferRenderbuffer(t.FRAMEBUFFER,ae,t.RENDERBUFFER,ee)}}else if(n.bindFramebuffer(t.FRAMEBUFFER,w.__webglFramebuffer),w.__webglDepthbuffer===void 0)w.__webglDepthbuffer=t.createRenderbuffer(),le(w.__webglDepthbuffer,b,!1);else{const ne=b.stencilBuffer?t.DEPTH_STENCIL_ATTACHMENT:t.DEPTH_ATTACHMENT,ae=w.__webglDepthbuffer;t.bindRenderbuffer(t.RENDERBUFFER,ae),t.framebufferRenderbuffer(t.FRAMEBUFFER,ne,t.RENDERBUFFER,ae)}n.bindFramebuffer(t.FRAMEBUFFER,null)}function te(b,w,G){const ne=i.get(b);w!==void 0&&ie(ne.__webglFramebuffer,b,b.texture,t.COLOR_ATTACHMENT0,t.TEXTURE_2D,0),G!==void 0&&oe(b)}function me(b){const w=b.texture,G=i.get(b),ne=i.get(w);b.addEventListener("dispose",A);const ae=b.textures,ee=b.isWebGLCubeRenderTarget===!0,Ie=ae.length>1;if(Ie||(ne.__webglTexture===void 0&&(ne.__webglTexture=t.createTexture()),ne.__version=w.version,o.memory.textures++),ee){G.__webglFramebuffer=[];for(let Se=0;Se<6;Se++)if(w.mipmaps&&w.mipmaps.length>0){G.__webglFramebuffer[Se]=[];for(let Pe=0;Pe<w.mipmaps.length;Pe++)G.__webglFramebuffer[Se][Pe]=t.createFramebuffer()}else G.__webglFramebuffer[Se]=t.createFramebuffer()}else{if(w.mipmaps&&w.mipmaps.length>0){G.__webglFramebuffer=[];for(let Se=0;Se<w.mipmaps.length;Se++)G.__webglFramebuffer[Se]=t.createFramebuffer()}else G.__webglFramebuffer=t.createFramebuffer();if(Ie)for(let Se=0,Pe=ae.length;Se<Pe;Se++){const tt=i.get(ae[Se]);tt.__webglTexture===void 0&&(tt.__webglTexture=t.createTexture(),o.memory.textures++)}if(b.samples>0&&He(b)===!1){G.__webglMultisampledFramebuffer=t.createFramebuffer(),G.__webglColorRenderbuffer=[],n.bindFramebuffer(t.FRAMEBUFFER,G.__webglMultisampledFramebuffer);for(let Se=0;Se<ae.length;Se++){const Pe=ae[Se];G.__webglColorRenderbuffer[Se]=t.createRenderbuffer(),t.bindRenderbuffer(t.RENDERBUFFER,G.__webglColorRenderbuffer[Se]);const tt=s.convert(Pe.format,Pe.colorSpace),K=s.convert(Pe.type),se=v(Pe.internalFormat,tt,K,Pe.colorSpace,b.isXRRenderTarget===!0),ve=ze(b);t.renderbufferStorageMultisample(t.RENDERBUFFER,ve,se,b.width,b.height),t.framebufferRenderbuffer(t.FRAMEBUFFER,t.COLOR_ATTACHMENT0+Se,t.RENDERBUFFER,G.__webglColorRenderbuffer[Se])}t.bindRenderbuffer(t.RENDERBUFFER,null),b.depthBuffer&&(G.__webglDepthRenderbuffer=t.createRenderbuffer(),le(G.__webglDepthRenderbuffer,b,!0)),n.bindFramebuffer(t.FRAMEBUFFER,null)}}if(ee){n.bindTexture(t.TEXTURE_CUBE_MAP,ne.__webglTexture),_e(t.TEXTURE_CUBE_MAP,w);for(let Se=0;Se<6;Se++)if(w.mipmaps&&w.mipmaps.length>0)for(let Pe=0;Pe<w.mipmaps.length;Pe++)ie(G.__webglFramebuffer[Se][Pe],b,w,t.COLOR_ATTACHMENT0,t.TEXTURE_CUBE_MAP_POSITIVE_X+Se,Pe);else ie(G.__webglFramebuffer[Se],b,w,t.COLOR_ATTACHMENT0,t.TEXTURE_CUBE_MAP_POSITIVE_X+Se,0);m(w)&&u(t.TEXTURE_CUBE_MAP),n.unbindTexture()}else if(Ie){for(let Se=0,Pe=ae.length;Se<Pe;Se++){const tt=ae[Se],K=i.get(tt);n.bindTexture(t.TEXTURE_2D,K.__webglTexture),_e(t.TEXTURE_2D,tt),ie(G.__webglFramebuffer,b,tt,t.COLOR_ATTACHMENT0+Se,t.TEXTURE_2D,0),m(tt)&&u(t.TEXTURE_2D)}n.unbindTexture()}else{let Se=t.TEXTURE_2D;if((b.isWebGL3DRenderTarget||b.isWebGLArrayRenderTarget)&&(Se=b.isWebGL3DRenderTarget?t.TEXTURE_3D:t.TEXTURE_2D_ARRAY),n.bindTexture(Se,ne.__webglTexture),_e(Se,w),w.mipmaps&&w.mipmaps.length>0)for(let Pe=0;Pe<w.mipmaps.length;Pe++)ie(G.__webglFramebuffer[Pe],b,w,t.COLOR_ATTACHMENT0,Se,Pe);else ie(G.__webglFramebuffer,b,w,t.COLOR_ATTACHMENT0,Se,0);m(w)&&u(Se),n.unbindTexture()}b.depthBuffer&&oe(b)}function pe(b){const w=b.textures;for(let G=0,ne=w.length;G<ne;G++){const ae=w[G];if(m(ae)){const ee=_(b),Ie=i.get(ae).__webglTexture;n.bindTexture(ee,Ie),u(ee),n.unbindTexture()}}}const Ue=[],L=[];function Xe(b){if(b.samples>0){if(He(b)===!1){const w=b.textures,G=b.width,ne=b.height;let ae=t.COLOR_BUFFER_BIT;const ee=b.stencilBuffer?t.DEPTH_STENCIL_ATTACHMENT:t.DEPTH_ATTACHMENT,Ie=i.get(b),Se=w.length>1;if(Se)for(let Pe=0;Pe<w.length;Pe++)n.bindFramebuffer(t.FRAMEBUFFER,Ie.__webglMultisampledFramebuffer),t.framebufferRenderbuffer(t.FRAMEBUFFER,t.COLOR_ATTACHMENT0+Pe,t.RENDERBUFFER,null),n.bindFramebuffer(t.FRAMEBUFFER,Ie.__webglFramebuffer),t.framebufferTexture2D(t.DRAW_FRAMEBUFFER,t.COLOR_ATTACHMENT0+Pe,t.TEXTURE_2D,null,0);n.bindFramebuffer(t.READ_FRAMEBUFFER,Ie.__webglMultisampledFramebuffer),n.bindFramebuffer(t.DRAW_FRAMEBUFFER,Ie.__webglFramebuffer);for(let Pe=0;Pe<w.length;Pe++){if(b.resolveDepthBuffer&&(b.depthBuffer&&(ae|=t.DEPTH_BUFFER_BIT),b.stencilBuffer&&b.resolveStencilBuffer&&(ae|=t.STENCIL_BUFFER_BIT)),Se){t.framebufferRenderbuffer(t.READ_FRAMEBUFFER,t.COLOR_ATTACHMENT0,t.RENDERBUFFER,Ie.__webglColorRenderbuffer[Pe]);const tt=i.get(w[Pe]).__webglTexture;t.framebufferTexture2D(t.DRAW_FRAMEBUFFER,t.COLOR_ATTACHMENT0,t.TEXTURE_2D,tt,0)}t.blitFramebuffer(0,0,G,ne,0,0,G,ne,ae,t.NEAREST),l===!0&&(Ue.length=0,L.length=0,Ue.push(t.COLOR_ATTACHMENT0+Pe),b.depthBuffer&&b.resolveDepthBuffer===!1&&(Ue.push(ee),L.push(ee),t.invalidateFramebuffer(t.DRAW_FRAMEBUFFER,L)),t.invalidateFramebuffer(t.READ_FRAMEBUFFER,Ue))}if(n.bindFramebuffer(t.READ_FRAMEBUFFER,null),n.bindFramebuffer(t.DRAW_FRAMEBUFFER,null),Se)for(let Pe=0;Pe<w.length;Pe++){n.bindFramebuffer(t.FRAMEBUFFER,Ie.__webglMultisampledFramebuffer),t.framebufferRenderbuffer(t.FRAMEBUFFER,t.COLOR_ATTACHMENT0+Pe,t.RENDERBUFFER,Ie.__webglColorRenderbuffer[Pe]);const tt=i.get(w[Pe]).__webglTexture;n.bindFramebuffer(t.FRAMEBUFFER,Ie.__webglFramebuffer),t.framebufferTexture2D(t.DRAW_FRAMEBUFFER,t.COLOR_ATTACHMENT0+Pe,t.TEXTURE_2D,tt,0)}n.bindFramebuffer(t.DRAW_FRAMEBUFFER,Ie.__webglMultisampledFramebuffer)}else if(b.depthBuffer&&b.resolveDepthBuffer===!1&&l){const w=b.stencilBuffer?t.DEPTH_STENCIL_ATTACHMENT:t.DEPTH_ATTACHMENT;t.invalidateFramebuffer(t.DRAW_FRAMEBUFFER,[w])}}}function ze(b){return Math.min(r.maxSamples,b.samples)}function He(b){const w=i.get(b);return b.samples>0&&e.has("WEBGL_multisampled_render_to_texture")===!0&&w.__useRenderToTexture!==!1}function Te(b){const w=o.render.frame;d.get(b)!==w&&(d.set(b,w),b.update())}function $e(b,w){const G=b.colorSpace,ne=b.format,ae=b.type;return b.isCompressedTexture===!0||b.isVideoTexture===!0||G!==qs&&G!==Zi&&(lt.getTransfer(G)===ft?(ne!==Qn||ae!==Ui)&&console.warn("THREE.WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType."):console.error("THREE.WebGLTextures: Unsupported texture color space:",G)),w}function we(b){return typeof HTMLImageElement<"u"&&b instanceof HTMLImageElement?(c.width=b.naturalWidth||b.width,c.height=b.naturalHeight||b.height):typeof VideoFrame<"u"&&b instanceof VideoFrame?(c.width=b.displayWidth,c.height=b.displayHeight):(c.width=b.width,c.height=b.height),c}this.allocateTextureUnit=H,this.resetTextureUnits=X,this.setTexture2D=Y,this.setTexture2DArray=V,this.setTexture3D=J,this.setTextureCube=N,this.rebindTextures=te,this.setupRenderTarget=me,this.updateRenderTargetMipmap=pe,this.updateMultisampleRenderTarget=Xe,this.setupDepthRenderbuffer=oe,this.setupFrameBufferTexture=ie,this.useMultisampledRTT=He}function gA(t,e){function n(i,r=Zi){let s;const o=lt.getTransfer(r);if(i===Ui)return t.UNSIGNED_BYTE;if(i===Mf)return t.UNSIGNED_SHORT_4_4_4_4;if(i===Ef)return t.UNSIGNED_SHORT_5_5_5_1;if(i===bv)return t.UNSIGNED_INT_5_9_9_9_REV;if(i===Av)return t.BYTE;if(i===Cv)return t.SHORT;if(i===ea)return t.UNSIGNED_SHORT;if(i===Sf)return t.INT;if(i===Vr)return t.UNSIGNED_INT;if(i===Ci)return t.FLOAT;if(i===oa)return t.HALF_FLOAT;if(i===Rv)return t.ALPHA;if(i===Pv)return t.RGB;if(i===Qn)return t.RGBA;if(i===Lv)return t.LUMINANCE;if(i===Nv)return t.LUMINANCE_ALPHA;if(i===Us)return t.DEPTH_COMPONENT;if(i===Ys)return t.DEPTH_STENCIL;if(i===Dv)return t.RED;if(i===wf)return t.RED_INTEGER;if(i===Iv)return t.RG;if(i===Tf)return t.RG_INTEGER;if(i===Af)return t.RGBA_INTEGER;if(i===_l||i===vl||i===xl||i===yl)if(o===ft)if(s=e.get("WEBGL_compressed_texture_s3tc_srgb"),s!==null){if(i===_l)return s.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(i===vl)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(i===xl)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(i===yl)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(s=e.get("WEBGL_compressed_texture_s3tc"),s!==null){if(i===_l)return s.COMPRESSED_RGB_S3TC_DXT1_EXT;if(i===vl)return s.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(i===xl)return s.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(i===yl)return s.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(i===qd||i===Kd||i===Zd||i===Jd)if(s=e.get("WEBGL_compressed_texture_pvrtc"),s!==null){if(i===qd)return s.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(i===Kd)return s.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(i===Zd)return s.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(i===Jd)return s.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(i===Qd||i===eh||i===th)if(s=e.get("WEBGL_compressed_texture_etc"),s!==null){if(i===Qd||i===eh)return o===ft?s.COMPRESSED_SRGB8_ETC2:s.COMPRESSED_RGB8_ETC2;if(i===th)return o===ft?s.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:s.COMPRESSED_RGBA8_ETC2_EAC}else return null;if(i===nh||i===ih||i===rh||i===sh||i===oh||i===ah||i===lh||i===ch||i===uh||i===dh||i===hh||i===fh||i===ph||i===mh)if(s=e.get("WEBGL_compressed_texture_astc"),s!==null){if(i===nh)return o===ft?s.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:s.COMPRESSED_RGBA_ASTC_4x4_KHR;if(i===ih)return o===ft?s.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:s.COMPRESSED_RGBA_ASTC_5x4_KHR;if(i===rh)return o===ft?s.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:s.COMPRESSED_RGBA_ASTC_5x5_KHR;if(i===sh)return o===ft?s.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:s.COMPRESSED_RGBA_ASTC_6x5_KHR;if(i===oh)return o===ft?s.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:s.COMPRESSED_RGBA_ASTC_6x6_KHR;if(i===ah)return o===ft?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:s.COMPRESSED_RGBA_ASTC_8x5_KHR;if(i===lh)return o===ft?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:s.COMPRESSED_RGBA_ASTC_8x6_KHR;if(i===ch)return o===ft?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:s.COMPRESSED_RGBA_ASTC_8x8_KHR;if(i===uh)return o===ft?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:s.COMPRESSED_RGBA_ASTC_10x5_KHR;if(i===dh)return o===ft?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:s.COMPRESSED_RGBA_ASTC_10x6_KHR;if(i===hh)return o===ft?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:s.COMPRESSED_RGBA_ASTC_10x8_KHR;if(i===fh)return o===ft?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:s.COMPRESSED_RGBA_ASTC_10x10_KHR;if(i===ph)return o===ft?s.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:s.COMPRESSED_RGBA_ASTC_12x10_KHR;if(i===mh)return o===ft?s.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:s.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(i===Sl||i===gh||i===_h)if(s=e.get("EXT_texture_compression_bptc"),s!==null){if(i===Sl)return o===ft?s.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:s.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(i===gh)return s.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(i===_h)return s.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(i===Uv||i===vh||i===xh||i===yh)if(s=e.get("EXT_texture_compression_rgtc"),s!==null){if(i===Sl)return s.COMPRESSED_RED_RGTC1_EXT;if(i===vh)return s.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(i===xh)return s.COMPRESSED_RED_GREEN_RGTC2_EXT;if(i===yh)return s.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;return i===$s?t.UNSIGNED_INT_24_8:t[i]!==void 0?t[i]:null}return{convert:n}}const _A={type:"move"};class Ou{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){return this._hand===null&&(this._hand=new Za,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1}),this._hand}getTargetRaySpace(){return this._targetRay===null&&(this._targetRay=new Za,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new O,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new O),this._targetRay}getGripSpace(){return this._grip===null&&(this._grip=new Za,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new O,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new O),this._grip}dispatchEvent(e){return this._targetRay!==null&&this._targetRay.dispatchEvent(e),this._grip!==null&&this._grip.dispatchEvent(e),this._hand!==null&&this._hand.dispatchEvent(e),this}connect(e){if(e&&e.hand){const n=this._hand;if(n)for(const i of e.hand.values())this._getHandJoint(n,i)}return this.dispatchEvent({type:"connected",data:e}),this}disconnect(e){return this.dispatchEvent({type:"disconnected",data:e}),this._targetRay!==null&&(this._targetRay.visible=!1),this._grip!==null&&(this._grip.visible=!1),this._hand!==null&&(this._hand.visible=!1),this}update(e,n,i){let r=null,s=null,o=null;const a=this._targetRay,l=this._grip,c=this._hand;if(e&&n.session.visibilityState!=="visible-blurred"){if(c&&e.hand){o=!0;for(const x of e.hand.values()){const m=n.getJointPose(x,i),u=this._getHandJoint(c,x);m!==null&&(u.matrix.fromArray(m.transform.matrix),u.matrix.decompose(u.position,u.rotation,u.scale),u.matrixWorldNeedsUpdate=!0,u.jointRadius=m.radius),u.visible=m!==null}const d=c.joints["index-finger-tip"],h=c.joints["thumb-tip"],f=d.position.distanceTo(h.position),p=.02,g=.005;c.inputState.pinching&&f>p+g?(c.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:e.handedness,target:this})):!c.inputState.pinching&&f<=p-g&&(c.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:e.handedness,target:this}))}else l!==null&&e.gripSpace&&(s=n.getPose(e.gripSpace,i),s!==null&&(l.matrix.fromArray(s.transform.matrix),l.matrix.decompose(l.position,l.rotation,l.scale),l.matrixWorldNeedsUpdate=!0,s.linearVelocity?(l.hasLinearVelocity=!0,l.linearVelocity.copy(s.linearVelocity)):l.hasLinearVelocity=!1,s.angularVelocity?(l.hasAngularVelocity=!0,l.angularVelocity.copy(s.angularVelocity)):l.hasAngularVelocity=!1));a!==null&&(r=n.getPose(e.targetRaySpace,i),r===null&&s!==null&&(r=s),r!==null&&(a.matrix.fromArray(r.transform.matrix),a.matrix.decompose(a.position,a.rotation,a.scale),a.matrixWorldNeedsUpdate=!0,r.linearVelocity?(a.hasLinearVelocity=!0,a.linearVelocity.copy(r.linearVelocity)):a.hasLinearVelocity=!1,r.angularVelocity?(a.hasAngularVelocity=!0,a.angularVelocity.copy(r.angularVelocity)):a.hasAngularVelocity=!1,this.dispatchEvent(_A)))}return a!==null&&(a.visible=r!==null),l!==null&&(l.visible=s!==null),c!==null&&(c.visible=o!==null),this}_getHandJoint(e,n){if(e.joints[n.jointName]===void 0){const i=new Za;i.matrixAutoUpdate=!1,i.visible=!1,e.joints[n.jointName]=i,e.add(i)}return e.joints[n.jointName]}}const vA=`
void main() {

	gl_Position = vec4( position, 1.0 );

}`,xA=`
uniform sampler2DArray depthColor;
uniform float depthWidth;
uniform float depthHeight;

void main() {

	vec2 coord = vec2( gl_FragCoord.x / depthWidth, gl_FragCoord.y / depthHeight );

	if ( coord.x >= 1.0 ) {

		gl_FragDepth = texture( depthColor, vec3( coord.x - 1.0, coord.y, 1 ) ).r;

	} else {

		gl_FragDepth = texture( depthColor, vec3( coord.x, coord.y, 0 ) ).r;

	}

}`;class yA{constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(e,n,i){if(this.texture===null){const r=new _n,s=e.properties.get(r);s.__webglTexture=n.texture,(n.depthNear!=i.depthNear||n.depthFar!=i.depthFar)&&(this.depthNear=n.depthNear,this.depthFar=n.depthFar),this.texture=r}}getMesh(e){if(this.texture!==null&&this.mesh===null){const n=e.cameras[0].viewport,i=new fr({vertexShader:vA,fragmentShader:xA,uniforms:{depthColor:{value:this.texture},depthWidth:{value:n.z},depthHeight:{value:n.w}}});this.mesh=new Tn(new Ec(20,20),i)}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}}class SA extends $r{constructor(e,n){super();const i=this;let r=null,s=1,o=null,a="local-floor",l=1,c=null,d=null,h=null,f=null,p=null,g=null;const x=new yA,m=n.getContextAttributes();let u=null,_=null;const v=[],M=[],R=new Fe;let C=null;const A=new Fn;A.viewport=new Rt;const P=new Fn;P.viewport=new Rt;const E=[A,P],S=new zM;let D=null,X=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(I){let z=v[I];return z===void 0&&(z=new Ou,v[I]=z),z.getTargetRaySpace()},this.getControllerGrip=function(I){let z=v[I];return z===void 0&&(z=new Ou,v[I]=z),z.getGripSpace()},this.getHand=function(I){let z=v[I];return z===void 0&&(z=new Ou,v[I]=z),z.getHandSpace()};function H(I){const z=M.indexOf(I.inputSource);if(z===-1)return;const ie=v[z];ie!==void 0&&(ie.update(I.inputSource,I.frame,c||o),ie.dispatchEvent({type:I.type,data:I.inputSource}))}function U(){r.removeEventListener("select",H),r.removeEventListener("selectstart",H),r.removeEventListener("selectend",H),r.removeEventListener("squeeze",H),r.removeEventListener("squeezestart",H),r.removeEventListener("squeezeend",H),r.removeEventListener("end",U),r.removeEventListener("inputsourceschange",Y);for(let I=0;I<v.length;I++){const z=M[I];z!==null&&(M[I]=null,v[I].disconnect(z))}D=null,X=null,x.reset(),e.setRenderTarget(u),p=null,f=null,h=null,r=null,_=null,Re.stop(),i.isPresenting=!1,e.setPixelRatio(C),e.setSize(R.width,R.height,!1),i.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(I){s=I,i.isPresenting===!0&&console.warn("THREE.WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(I){a=I,i.isPresenting===!0&&console.warn("THREE.WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return c||o},this.setReferenceSpace=function(I){c=I},this.getBaseLayer=function(){return f!==null?f:p},this.getBinding=function(){return h},this.getFrame=function(){return g},this.getSession=function(){return r},this.setSession=async function(I){if(r=I,r!==null){if(u=e.getRenderTarget(),r.addEventListener("select",H),r.addEventListener("selectstart",H),r.addEventListener("selectend",H),r.addEventListener("squeeze",H),r.addEventListener("squeezestart",H),r.addEventListener("squeezeend",H),r.addEventListener("end",U),r.addEventListener("inputsourceschange",Y),m.xrCompatible!==!0&&await n.makeXRCompatible(),C=e.getPixelRatio(),e.getSize(R),r.renderState.layers===void 0){const z={antialias:m.antialias,alpha:!0,depth:m.depth,stencil:m.stencil,framebufferScaleFactor:s};p=new XRWebGLLayer(r,n,z),r.updateRenderState({baseLayer:p}),e.setPixelRatio(1),e.setSize(p.framebufferWidth,p.framebufferHeight,!1),_=new Gr(p.framebufferWidth,p.framebufferHeight,{format:Qn,type:Ui,colorSpace:e.outputColorSpace,stencilBuffer:m.stencil})}else{let z=null,ie=null,le=null;m.depth&&(le=m.stencil?n.DEPTH24_STENCIL8:n.DEPTH_COMPONENT24,z=m.stencil?Ys:Us,ie=m.stencil?$s:Vr);const ye={colorFormat:n.RGBA8,depthFormat:le,scaleFactor:s};h=new XRWebGLBinding(r,n),f=h.createProjectionLayer(ye),r.updateRenderState({layers:[f]}),e.setPixelRatio(1),e.setSize(f.textureWidth,f.textureHeight,!1),_=new Gr(f.textureWidth,f.textureHeight,{format:Qn,type:Ui,depthTexture:new Yv(f.textureWidth,f.textureHeight,ie,void 0,void 0,void 0,void 0,void 0,void 0,z),stencilBuffer:m.stencil,colorSpace:e.outputColorSpace,samples:m.antialias?4:0,resolveDepthBuffer:f.ignoreDepthValues===!1})}_.isXRRenderTarget=!0,this.setFoveation(l),c=null,o=await r.requestReferenceSpace(a),Re.setContext(r),Re.start(),i.isPresenting=!0,i.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(r!==null)return r.environmentBlendMode},this.getDepthTexture=function(){return x.getDepthTexture()};function Y(I){for(let z=0;z<I.removed.length;z++){const ie=I.removed[z],le=M.indexOf(ie);le>=0&&(M[le]=null,v[le].disconnect(ie))}for(let z=0;z<I.added.length;z++){const ie=I.added[z];let le=M.indexOf(ie);if(le===-1){for(let oe=0;oe<v.length;oe++)if(oe>=M.length){M.push(ie),le=oe;break}else if(M[oe]===null){M[oe]=ie,le=oe;break}if(le===-1)break}const ye=v[le];ye&&ye.connect(ie)}}const V=new O,J=new O;function N(I,z,ie){V.setFromMatrixPosition(z.matrixWorld),J.setFromMatrixPosition(ie.matrixWorld);const le=V.distanceTo(J),ye=z.projectionMatrix.elements,oe=ie.projectionMatrix.elements,te=ye[14]/(ye[10]-1),me=ye[14]/(ye[10]+1),pe=(ye[9]+1)/ye[5],Ue=(ye[9]-1)/ye[5],L=(ye[8]-1)/ye[0],Xe=(oe[8]+1)/oe[0],ze=te*L,He=te*Xe,Te=le/(-L+Xe),$e=Te*-L;if(z.matrixWorld.decompose(I.position,I.quaternion,I.scale),I.translateX($e),I.translateZ(Te),I.matrixWorld.compose(I.position,I.quaternion,I.scale),I.matrixWorldInverse.copy(I.matrixWorld).invert(),ye[10]===-1)I.projectionMatrix.copy(z.projectionMatrix),I.projectionMatrixInverse.copy(z.projectionMatrixInverse);else{const we=te+Te,b=me+Te,w=ze-$e,G=He+(le-$e),ne=pe*me/b*we,ae=Ue*me/b*we;I.projectionMatrix.makePerspective(w,G,ne,ae,we,b),I.projectionMatrixInverse.copy(I.projectionMatrix).invert()}}function j(I,z){z===null?I.matrixWorld.copy(I.matrix):I.matrixWorld.multiplyMatrices(z.matrixWorld,I.matrix),I.matrixWorldInverse.copy(I.matrixWorld).invert()}this.updateCamera=function(I){if(r===null)return;let z=I.near,ie=I.far;x.texture!==null&&(x.depthNear>0&&(z=x.depthNear),x.depthFar>0&&(ie=x.depthFar)),S.near=P.near=A.near=z,S.far=P.far=A.far=ie,(D!==S.near||X!==S.far)&&(r.updateRenderState({depthNear:S.near,depthFar:S.far}),D=S.near,X=S.far),A.layers.mask=I.layers.mask|2,P.layers.mask=I.layers.mask|4,S.layers.mask=A.layers.mask|P.layers.mask;const le=I.parent,ye=S.cameras;j(S,le);for(let oe=0;oe<ye.length;oe++)j(ye[oe],le);ye.length===2?N(S,A,P):S.projectionMatrix.copy(A.projectionMatrix),Z(I,S,le)};function Z(I,z,ie){ie===null?I.matrix.copy(z.matrixWorld):(I.matrix.copy(ie.matrixWorld),I.matrix.invert(),I.matrix.multiply(z.matrixWorld)),I.matrix.decompose(I.position,I.quaternion,I.scale),I.updateMatrixWorld(!0),I.projectionMatrix.copy(z.projectionMatrix),I.projectionMatrixInverse.copy(z.projectionMatrixInverse),I.isPerspectiveCamera&&(I.fov=Sh*2*Math.atan(1/I.projectionMatrix.elements[5]),I.zoom=1)}this.getCamera=function(){return S},this.getFoveation=function(){if(!(f===null&&p===null))return l},this.setFoveation=function(I){l=I,f!==null&&(f.fixedFoveation=I),p!==null&&p.fixedFoveation!==void 0&&(p.fixedFoveation=I)},this.hasDepthSensing=function(){return x.texture!==null},this.getDepthSensingMesh=function(){return x.getMesh(S)};let fe=null;function _e(I,z){if(d=z.getViewerPose(c||o),g=z,d!==null){const ie=d.views;p!==null&&(e.setRenderTargetFramebuffer(_,p.framebuffer),e.setRenderTarget(_));let le=!1;ie.length!==S.cameras.length&&(S.cameras.length=0,le=!0);for(let oe=0;oe<ie.length;oe++){const te=ie[oe];let me=null;if(p!==null)me=p.getViewport(te);else{const Ue=h.getViewSubImage(f,te);me=Ue.viewport,oe===0&&(e.setRenderTargetTextures(_,Ue.colorTexture,f.ignoreDepthValues?void 0:Ue.depthStencilTexture),e.setRenderTarget(_))}let pe=E[oe];pe===void 0&&(pe=new Fn,pe.layers.enable(oe),pe.viewport=new Rt,E[oe]=pe),pe.matrix.fromArray(te.transform.matrix),pe.matrix.decompose(pe.position,pe.quaternion,pe.scale),pe.projectionMatrix.fromArray(te.projectionMatrix),pe.projectionMatrixInverse.copy(pe.projectionMatrix).invert(),pe.viewport.set(me.x,me.y,me.width,me.height),oe===0&&(S.matrix.copy(pe.matrix),S.matrix.decompose(S.position,S.quaternion,S.scale)),le===!0&&S.cameras.push(pe)}const ye=r.enabledFeatures;if(ye&&ye.includes("depth-sensing")){const oe=h.getDepthInformation(ie[0]);oe&&oe.isValid&&oe.texture&&x.init(e,oe,r.renderState)}}for(let ie=0;ie<v.length;ie++){const le=M[ie],ye=v[ie];le!==null&&ye!==void 0&&ye.update(le,z,c||o)}fe&&fe(I,z),z.detectedPlanes&&i.dispatchEvent({type:"planesdetected",data:z}),g=null}const Re=new Qv;Re.setAnimationLoop(_e),this.setAnimationLoop=function(I){fe=I},this.dispose=function(){}}}const wr=new hi,MA=new mt;function EA(t,e){function n(m,u){m.matrixAutoUpdate===!0&&m.updateMatrix(),u.value.copy(m.matrix)}function i(m,u){u.color.getRGB(m.fogColor.value,Wv(t)),u.isFog?(m.fogNear.value=u.near,m.fogFar.value=u.far):u.isFogExp2&&(m.fogDensity.value=u.density)}function r(m,u,_,v,M){u.isMeshBasicMaterial||u.isMeshLambertMaterial?s(m,u):u.isMeshToonMaterial?(s(m,u),h(m,u)):u.isMeshPhongMaterial?(s(m,u),d(m,u)):u.isMeshStandardMaterial?(s(m,u),f(m,u),u.isMeshPhysicalMaterial&&p(m,u,M)):u.isMeshMatcapMaterial?(s(m,u),g(m,u)):u.isMeshDepthMaterial?s(m,u):u.isMeshDistanceMaterial?(s(m,u),x(m,u)):u.isMeshNormalMaterial?s(m,u):u.isLineBasicMaterial?(o(m,u),u.isLineDashedMaterial&&a(m,u)):u.isPointsMaterial?l(m,u,_,v):u.isSpriteMaterial?c(m,u):u.isShadowMaterial?(m.color.value.copy(u.color),m.opacity.value=u.opacity):u.isShaderMaterial&&(u.uniformsNeedUpdate=!1)}function s(m,u){m.opacity.value=u.opacity,u.color&&m.diffuse.value.copy(u.color),u.emissive&&m.emissive.value.copy(u.emissive).multiplyScalar(u.emissiveIntensity),u.map&&(m.map.value=u.map,n(u.map,m.mapTransform)),u.alphaMap&&(m.alphaMap.value=u.alphaMap,n(u.alphaMap,m.alphaMapTransform)),u.bumpMap&&(m.bumpMap.value=u.bumpMap,n(u.bumpMap,m.bumpMapTransform),m.bumpScale.value=u.bumpScale,u.side===gn&&(m.bumpScale.value*=-1)),u.normalMap&&(m.normalMap.value=u.normalMap,n(u.normalMap,m.normalMapTransform),m.normalScale.value.copy(u.normalScale),u.side===gn&&m.normalScale.value.negate()),u.displacementMap&&(m.displacementMap.value=u.displacementMap,n(u.displacementMap,m.displacementMapTransform),m.displacementScale.value=u.displacementScale,m.displacementBias.value=u.displacementBias),u.emissiveMap&&(m.emissiveMap.value=u.emissiveMap,n(u.emissiveMap,m.emissiveMapTransform)),u.specularMap&&(m.specularMap.value=u.specularMap,n(u.specularMap,m.specularMapTransform)),u.alphaTest>0&&(m.alphaTest.value=u.alphaTest);const _=e.get(u),v=_.envMap,M=_.envMapRotation;v&&(m.envMap.value=v,wr.copy(M),wr.x*=-1,wr.y*=-1,wr.z*=-1,v.isCubeTexture&&v.isRenderTargetTexture===!1&&(wr.y*=-1,wr.z*=-1),m.envMapRotation.value.setFromMatrix4(MA.makeRotationFromEuler(wr)),m.flipEnvMap.value=v.isCubeTexture&&v.isRenderTargetTexture===!1?-1:1,m.reflectivity.value=u.reflectivity,m.ior.value=u.ior,m.refractionRatio.value=u.refractionRatio),u.lightMap&&(m.lightMap.value=u.lightMap,m.lightMapIntensity.value=u.lightMapIntensity,n(u.lightMap,m.lightMapTransform)),u.aoMap&&(m.aoMap.value=u.aoMap,m.aoMapIntensity.value=u.aoMapIntensity,n(u.aoMap,m.aoMapTransform))}function o(m,u){m.diffuse.value.copy(u.color),m.opacity.value=u.opacity,u.map&&(m.map.value=u.map,n(u.map,m.mapTransform))}function a(m,u){m.dashSize.value=u.dashSize,m.totalSize.value=u.dashSize+u.gapSize,m.scale.value=u.scale}function l(m,u,_,v){m.diffuse.value.copy(u.color),m.opacity.value=u.opacity,m.size.value=u.size*_,m.scale.value=v*.5,u.map&&(m.map.value=u.map,n(u.map,m.uvTransform)),u.alphaMap&&(m.alphaMap.value=u.alphaMap,n(u.alphaMap,m.alphaMapTransform)),u.alphaTest>0&&(m.alphaTest.value=u.alphaTest)}function c(m,u){m.diffuse.value.copy(u.color),m.opacity.value=u.opacity,m.rotation.value=u.rotation,u.map&&(m.map.value=u.map,n(u.map,m.mapTransform)),u.alphaMap&&(m.alphaMap.value=u.alphaMap,n(u.alphaMap,m.alphaMapTransform)),u.alphaTest>0&&(m.alphaTest.value=u.alphaTest)}function d(m,u){m.specular.value.copy(u.specular),m.shininess.value=Math.max(u.shininess,1e-4)}function h(m,u){u.gradientMap&&(m.gradientMap.value=u.gradientMap)}function f(m,u){m.metalness.value=u.metalness,u.metalnessMap&&(m.metalnessMap.value=u.metalnessMap,n(u.metalnessMap,m.metalnessMapTransform)),m.roughness.value=u.roughness,u.roughnessMap&&(m.roughnessMap.value=u.roughnessMap,n(u.roughnessMap,m.roughnessMapTransform)),u.envMap&&(m.envMapIntensity.value=u.envMapIntensity)}function p(m,u,_){m.ior.value=u.ior,u.sheen>0&&(m.sheenColor.value.copy(u.sheenColor).multiplyScalar(u.sheen),m.sheenRoughness.value=u.sheenRoughness,u.sheenColorMap&&(m.sheenColorMap.value=u.sheenColorMap,n(u.sheenColorMap,m.sheenColorMapTransform)),u.sheenRoughnessMap&&(m.sheenRoughnessMap.value=u.sheenRoughnessMap,n(u.sheenRoughnessMap,m.sheenRoughnessMapTransform))),u.clearcoat>0&&(m.clearcoat.value=u.clearcoat,m.clearcoatRoughness.value=u.clearcoatRoughness,u.clearcoatMap&&(m.clearcoatMap.value=u.clearcoatMap,n(u.clearcoatMap,m.clearcoatMapTransform)),u.clearcoatRoughnessMap&&(m.clearcoatRoughnessMap.value=u.clearcoatRoughnessMap,n(u.clearcoatRoughnessMap,m.clearcoatRoughnessMapTransform)),u.clearcoatNormalMap&&(m.clearcoatNormalMap.value=u.clearcoatNormalMap,n(u.clearcoatNormalMap,m.clearcoatNormalMapTransform),m.clearcoatNormalScale.value.copy(u.clearcoatNormalScale),u.side===gn&&m.clearcoatNormalScale.value.negate())),u.dispersion>0&&(m.dispersion.value=u.dispersion),u.iridescence>0&&(m.iridescence.value=u.iridescence,m.iridescenceIOR.value=u.iridescenceIOR,m.iridescenceThicknessMinimum.value=u.iridescenceThicknessRange[0],m.iridescenceThicknessMaximum.value=u.iridescenceThicknessRange[1],u.iridescenceMap&&(m.iridescenceMap.value=u.iridescenceMap,n(u.iridescenceMap,m.iridescenceMapTransform)),u.iridescenceThicknessMap&&(m.iridescenceThicknessMap.value=u.iridescenceThicknessMap,n(u.iridescenceThicknessMap,m.iridescenceThicknessMapTransform))),u.transmission>0&&(m.transmission.value=u.transmission,m.transmissionSamplerMap.value=_.texture,m.transmissionSamplerSize.value.set(_.width,_.height),u.transmissionMap&&(m.transmissionMap.value=u.transmissionMap,n(u.transmissionMap,m.transmissionMapTransform)),m.thickness.value=u.thickness,u.thicknessMap&&(m.thicknessMap.value=u.thicknessMap,n(u.thicknessMap,m.thicknessMapTransform)),m.attenuationDistance.value=u.attenuationDistance,m.attenuationColor.value.copy(u.attenuationColor)),u.anisotropy>0&&(m.anisotropyVector.value.set(u.anisotropy*Math.cos(u.anisotropyRotation),u.anisotropy*Math.sin(u.anisotropyRotation)),u.anisotropyMap&&(m.anisotropyMap.value=u.anisotropyMap,n(u.anisotropyMap,m.anisotropyMapTransform))),m.specularIntensity.value=u.specularIntensity,m.specularColor.value.copy(u.specularColor),u.specularColorMap&&(m.specularColorMap.value=u.specularColorMap,n(u.specularColorMap,m.specularColorMapTransform)),u.specularIntensityMap&&(m.specularIntensityMap.value=u.specularIntensityMap,n(u.specularIntensityMap,m.specularIntensityMapTransform))}function g(m,u){u.matcap&&(m.matcap.value=u.matcap)}function x(m,u){const _=e.get(u).light;m.referencePosition.value.setFromMatrixPosition(_.matrixWorld),m.nearDistance.value=_.shadow.camera.near,m.farDistance.value=_.shadow.camera.far}return{refreshFogUniforms:i,refreshMaterialUniforms:r}}function wA(t,e,n,i){let r={},s={},o=[];const a=t.getParameter(t.MAX_UNIFORM_BUFFER_BINDINGS);function l(_,v){const M=v.program;i.uniformBlockBinding(_,M)}function c(_,v){let M=r[_.id];M===void 0&&(g(_),M=d(_),r[_.id]=M,_.addEventListener("dispose",m));const R=v.program;i.updateUBOMapping(_,R);const C=e.render.frame;s[_.id]!==C&&(f(_),s[_.id]=C)}function d(_){const v=h();_.__bindingPointIndex=v;const M=t.createBuffer(),R=_.__size,C=_.usage;return t.bindBuffer(t.UNIFORM_BUFFER,M),t.bufferData(t.UNIFORM_BUFFER,R,C),t.bindBuffer(t.UNIFORM_BUFFER,null),t.bindBufferBase(t.UNIFORM_BUFFER,v,M),M}function h(){for(let _=0;_<a;_++)if(o.indexOf(_)===-1)return o.push(_),_;return console.error("THREE.WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function f(_){const v=r[_.id],M=_.uniforms,R=_.__cache;t.bindBuffer(t.UNIFORM_BUFFER,v);for(let C=0,A=M.length;C<A;C++){const P=Array.isArray(M[C])?M[C]:[M[C]];for(let E=0,S=P.length;E<S;E++){const D=P[E];if(p(D,C,E,R)===!0){const X=D.__offset,H=Array.isArray(D.value)?D.value:[D.value];let U=0;for(let Y=0;Y<H.length;Y++){const V=H[Y],J=x(V);typeof V=="number"||typeof V=="boolean"?(D.__data[0]=V,t.bufferSubData(t.UNIFORM_BUFFER,X+U,D.__data)):V.isMatrix3?(D.__data[0]=V.elements[0],D.__data[1]=V.elements[1],D.__data[2]=V.elements[2],D.__data[3]=0,D.__data[4]=V.elements[3],D.__data[5]=V.elements[4],D.__data[6]=V.elements[5],D.__data[7]=0,D.__data[8]=V.elements[6],D.__data[9]=V.elements[7],D.__data[10]=V.elements[8],D.__data[11]=0):(V.toArray(D.__data,U),U+=J.storage/Float32Array.BYTES_PER_ELEMENT)}t.bufferSubData(t.UNIFORM_BUFFER,X,D.__data)}}}t.bindBuffer(t.UNIFORM_BUFFER,null)}function p(_,v,M,R){const C=_.value,A=v+"_"+M;if(R[A]===void 0)return typeof C=="number"||typeof C=="boolean"?R[A]=C:R[A]=C.clone(),!0;{const P=R[A];if(typeof C=="number"||typeof C=="boolean"){if(P!==C)return R[A]=C,!0}else if(P.equals(C)===!1)return P.copy(C),!0}return!1}function g(_){const v=_.uniforms;let M=0;const R=16;for(let A=0,P=v.length;A<P;A++){const E=Array.isArray(v[A])?v[A]:[v[A]];for(let S=0,D=E.length;S<D;S++){const X=E[S],H=Array.isArray(X.value)?X.value:[X.value];for(let U=0,Y=H.length;U<Y;U++){const V=H[U],J=x(V),N=M%R,j=N%J.boundary,Z=N+j;M+=j,Z!==0&&R-Z<J.storage&&(M+=R-Z),X.__data=new Float32Array(J.storage/Float32Array.BYTES_PER_ELEMENT),X.__offset=M,M+=J.storage}}}const C=M%R;return C>0&&(M+=R-C),_.__size=M,_.__cache={},this}function x(_){const v={boundary:0,storage:0};return typeof _=="number"||typeof _=="boolean"?(v.boundary=4,v.storage=4):_.isVector2?(v.boundary=8,v.storage=8):_.isVector3||_.isColor?(v.boundary=16,v.storage=12):_.isVector4?(v.boundary=16,v.storage=16):_.isMatrix3?(v.boundary=48,v.storage=48):_.isMatrix4?(v.boundary=64,v.storage=64):_.isTexture?console.warn("THREE.WebGLRenderer: Texture samplers can not be part of an uniforms group."):console.warn("THREE.WebGLRenderer: Unsupported uniform value type.",_),v}function m(_){const v=_.target;v.removeEventListener("dispose",m);const M=o.indexOf(v.__bindingPointIndex);o.splice(M,1),t.deleteBuffer(r[v.id]),delete r[v.id],delete s[v.id]}function u(){for(const _ in r)t.deleteBuffer(r[_]);o=[],r={},s={}}return{bind:l,update:c,dispose:u}}class TA{constructor(e={}){const{canvas:n=WS(),context:i=null,depth:r=!0,stencil:s=!1,alpha:o=!1,antialias:a=!1,premultipliedAlpha:l=!0,preserveDrawingBuffer:c=!1,powerPreference:d="default",failIfMajorPerformanceCaveat:h=!1,reverseDepthBuffer:f=!1}=e;this.isWebGLRenderer=!0;let p;if(i!==null){if(typeof WebGLRenderingContext<"u"&&i instanceof WebGLRenderingContext)throw new Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");p=i.getContextAttributes().alpha}else p=o;const g=new Uint32Array(4),x=new Int32Array(4);let m=null,u=null;const _=[],v=[];this.domElement=n,this.debug={checkShaderErrors:!0,onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this._outputColorSpace=In,this.toneMapping=cr,this.toneMappingExposure=1;const M=this;let R=!1,C=0,A=0,P=null,E=-1,S=null;const D=new Rt,X=new Rt;let H=null;const U=new ct(0);let Y=0,V=n.width,J=n.height,N=1,j=null,Z=null;const fe=new Rt(0,0,V,J),_e=new Rt(0,0,V,J);let Re=!1;const I=new bf;let z=!1,ie=!1;const le=new mt,ye=new mt,oe=new O,te=new Rt,me={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0};let pe=!1;function Ue(){return P===null?N:1}let L=i;function Xe(T,k){return n.getContext(T,k)}try{const T={alpha:!0,depth:r,stencil:s,antialias:a,premultipliedAlpha:l,preserveDrawingBuffer:c,powerPreference:d,failIfMajorPerformanceCaveat:h};if("setAttribute"in n&&n.setAttribute("data-engine",`three.js r${yf}`),n.addEventListener("webglcontextlost",re,!1),n.addEventListener("webglcontextrestored",be,!1),n.addEventListener("webglcontextcreationerror",Ae,!1),L===null){const k="webgl2";if(L=Xe(k,T),L===null)throw Xe(k)?new Error("Error creating WebGL context with your selected attributes."):new Error("Error creating WebGL context.")}}catch(T){throw console.error("THREE.WebGLRenderer: "+T.message),T}let ze,He,Te,$e,we,b,w,G,ne,ae,ee,Ie,Se,Pe,tt,K,se,ve,Me,ue,je,Ve,Qe,F;function xe(){ze=new I1(L),ze.init(),Ve=new gA(L,ze),He=new b1(L,ze,e,Ve),Te=new pA(L,ze),He.reverseDepthBuffer&&f&&Te.buffers.depth.setReversed(!0),$e=new F1(L),we=new tA,b=new mA(L,ze,Te,we,He,Ve,$e),w=new P1(M),G=new D1(M),ne=new jM(L),Qe=new A1(L,ne),ae=new U1(L,ne,$e,Qe),ee=new B1(L,ae,ne,$e),Me=new k1(L,He,b),K=new R1(we),Ie=new eA(M,w,G,ze,He,Qe,K),Se=new EA(M,we),Pe=new iA,tt=new cA(ze),ve=new T1(M,w,G,Te,ee,p,l),se=new hA(M,ee,He),F=new wA(L,$e,He,Te),ue=new C1(L,ze,$e),je=new O1(L,ze,$e),$e.programs=Ie.programs,M.capabilities=He,M.extensions=ze,M.properties=we,M.renderLists=Pe,M.shadowMap=se,M.state=Te,M.info=$e}xe();const q=new SA(M,L);this.xr=q,this.getContext=function(){return L},this.getContextAttributes=function(){return L.getContextAttributes()},this.forceContextLoss=function(){const T=ze.get("WEBGL_lose_context");T&&T.loseContext()},this.forceContextRestore=function(){const T=ze.get("WEBGL_lose_context");T&&T.restoreContext()},this.getPixelRatio=function(){return N},this.setPixelRatio=function(T){T!==void 0&&(N=T,this.setSize(V,J,!1))},this.getSize=function(T){return T.set(V,J)},this.setSize=function(T,k,W=!0){if(q.isPresenting){console.warn("THREE.WebGLRenderer: Can't change size while VR device is presenting.");return}V=T,J=k,n.width=Math.floor(T*N),n.height=Math.floor(k*N),W===!0&&(n.style.width=T+"px",n.style.height=k+"px"),this.setViewport(0,0,T,k)},this.getDrawingBufferSize=function(T){return T.set(V*N,J*N).floor()},this.setDrawingBufferSize=function(T,k,W){V=T,J=k,N=W,n.width=Math.floor(T*W),n.height=Math.floor(k*W),this.setViewport(0,0,T,k)},this.getCurrentViewport=function(T){return T.copy(D)},this.getViewport=function(T){return T.copy(fe)},this.setViewport=function(T,k,W,$){T.isVector4?fe.set(T.x,T.y,T.z,T.w):fe.set(T,k,W,$),Te.viewport(D.copy(fe).multiplyScalar(N).round())},this.getScissor=function(T){return T.copy(_e)},this.setScissor=function(T,k,W,$){T.isVector4?_e.set(T.x,T.y,T.z,T.w):_e.set(T,k,W,$),Te.scissor(X.copy(_e).multiplyScalar(N).round())},this.getScissorTest=function(){return Re},this.setScissorTest=function(T){Te.setScissorTest(Re=T)},this.setOpaqueSort=function(T){j=T},this.setTransparentSort=function(T){Z=T},this.getClearColor=function(T){return T.copy(ve.getClearColor())},this.setClearColor=function(){ve.setClearColor.apply(ve,arguments)},this.getClearAlpha=function(){return ve.getClearAlpha()},this.setClearAlpha=function(){ve.setClearAlpha.apply(ve,arguments)},this.clear=function(T=!0,k=!0,W=!0){let $=0;if(T){let B=!1;if(P!==null){const de=P.texture.format;B=de===Af||de===Tf||de===wf}if(B){const de=P.texture.type,Ce=de===Ui||de===Vr||de===ea||de===$s||de===Mf||de===Ef,De=ve.getClearColor(),Oe=ve.getClearAlpha(),Ye=De.r,qe=De.g,Ge=De.b;Ce?(g[0]=Ye,g[1]=qe,g[2]=Ge,g[3]=Oe,L.clearBufferuiv(L.COLOR,0,g)):(x[0]=Ye,x[1]=qe,x[2]=Ge,x[3]=Oe,L.clearBufferiv(L.COLOR,0,x))}else $|=L.COLOR_BUFFER_BIT}k&&($|=L.DEPTH_BUFFER_BIT),W&&($|=L.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295)),L.clear($)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.dispose=function(){n.removeEventListener("webglcontextlost",re,!1),n.removeEventListener("webglcontextrestored",be,!1),n.removeEventListener("webglcontextcreationerror",Ae,!1),ve.dispose(),Pe.dispose(),tt.dispose(),we.dispose(),w.dispose(),G.dispose(),ee.dispose(),Qe.dispose(),F.dispose(),Ie.dispose(),q.dispose(),q.removeEventListener("sessionstart",ua),q.removeEventListener("sessionend",da),fi.stop()};function re(T){T.preventDefault(),console.log("THREE.WebGLRenderer: Context Lost."),R=!0}function be(){console.log("THREE.WebGLRenderer: Context Restored."),R=!1;const T=$e.autoReset,k=se.enabled,W=se.autoUpdate,$=se.needsUpdate,B=se.type;xe(),$e.autoReset=T,se.enabled=k,se.autoUpdate=W,se.needsUpdate=$,se.type=B}function Ae(T){console.error("THREE.WebGLRenderer: A WebGL context could not be created. Reason: ",T.statusMessage)}function Ke(T){const k=T.target;k.removeEventListener("dispose",Ke),xt(k)}function xt(T){Lt(T),we.remove(T)}function Lt(T){const k=we.get(T).programs;k!==void 0&&(k.forEach(function(W){Ie.releaseProgram(W)}),T.isShaderMaterial&&Ie.releaseShaderCache(T))}this.renderBufferDirect=function(T,k,W,$,B,de){k===null&&(k=me);const Ce=B.isMesh&&B.matrixWorld.determinant()<0,De=ke(T,k,W,$,B);Te.setMaterial($,Ce);let Oe=W.index,Ye=1;if($.wireframe===!0){if(Oe=ae.getWireframeAttribute(W),Oe===void 0)return;Ye=2}const qe=W.drawRange,Ge=W.attributes.position;let st=qe.start*Ye,ut=(qe.start+qe.count)*Ye;de!==null&&(st=Math.max(st,de.start*Ye),ut=Math.min(ut,(de.start+de.count)*Ye)),Oe!==null?(st=Math.max(st,0),ut=Math.min(ut,Oe.count)):Ge!=null&&(st=Math.max(st,0),ut=Math.min(ut,Ge.count));const Nt=ut-st;if(Nt<0||Nt===1/0)return;Qe.setup(B,$,De,W,Oe);let Ct,at=ue;if(Oe!==null&&(Ct=ne.get(Oe),at=je,at.setIndex(Ct)),B.isMesh)$.wireframe===!0?(Te.setLineWidth($.wireframeLinewidth*Ue()),at.setMode(L.LINES)):at.setMode(L.TRIANGLES);else if(B.isLine){let We=$.linewidth;We===void 0&&(We=1),Te.setLineWidth(We*Ue()),B.isLineSegments?at.setMode(L.LINES):B.isLineLoop?at.setMode(L.LINE_LOOP):at.setMode(L.LINE_STRIP)}else B.isPoints?at.setMode(L.POINTS):B.isSprite&&at.setMode(L.TRIANGLES);if(B.isBatchedMesh)if(B._multiDrawInstances!==null)at.renderMultiDrawInstances(B._multiDrawStarts,B._multiDrawCounts,B._multiDrawCount,B._multiDrawInstances);else if(ze.get("WEBGL_multi_draw"))at.renderMultiDraw(B._multiDrawStarts,B._multiDrawCounts,B._multiDrawCount);else{const We=B._multiDrawStarts,jt=B._multiDrawCounts,dt=B._multiDrawCount,Gn=Oe?ne.get(Oe).bytesPerElement:1,qr=we.get($).currentProgram.getUniforms();for(let yn=0;yn<dt;yn++)qr.setValue(L,"_gl_DrawID",yn),at.render(We[yn]/Gn,jt[yn])}else if(B.isInstancedMesh)at.renderInstances(st,Nt,B.count);else if(W.isInstancedBufferGeometry){const We=W._maxInstanceCount!==void 0?W._maxInstanceCount:1/0,jt=Math.min(W.instanceCount,We);at.renderInstances(st,Nt,jt)}else at.render(st,Nt)};function it(T,k,W){T.transparent===!0&&T.side===wi&&T.forceSinglePass===!1?(T.side=gn,T.needsUpdate=!0,Be(T,k,W),T.side=hr,T.needsUpdate=!0,Be(T,k,W),T.side=wi):Be(T,k,W)}this.compile=function(T,k,W=null){W===null&&(W=T),u=tt.get(W),u.init(k),v.push(u),W.traverseVisible(function(B){B.isLight&&B.layers.test(k.layers)&&(u.pushLight(B),B.castShadow&&u.pushShadow(B))}),T!==W&&T.traverseVisible(function(B){B.isLight&&B.layers.test(k.layers)&&(u.pushLight(B),B.castShadow&&u.pushShadow(B))}),u.setupLights();const $=new Set;return T.traverse(function(B){if(!(B.isMesh||B.isPoints||B.isLine||B.isSprite))return;const de=B.material;if(de)if(Array.isArray(de))for(let Ce=0;Ce<de.length;Ce++){const De=de[Ce];it(De,W,B),$.add(De)}else it(de,W,B),$.add(de)}),v.pop(),u=null,$},this.compileAsync=function(T,k,W=null){const $=this.compile(T,k,W);return new Promise(B=>{function de(){if($.forEach(function(Ce){we.get(Ce).currentProgram.isReady()&&$.delete(Ce)}),$.size===0){B(T);return}setTimeout(de,10)}ze.get("KHR_parallel_shader_compile")!==null?de():setTimeout(de,10)})};let xn=null;function Vn(T){xn&&xn(T)}function ua(){fi.stop()}function da(){fi.start()}const fi=new Qv;fi.setAnimationLoop(Vn),typeof self<"u"&&fi.setContext(self),this.setAnimationLoop=function(T){xn=T,q.setAnimationLoop(T),T===null?fi.stop():fi.start()},q.addEventListener("sessionstart",ua),q.addEventListener("sessionend",da),this.render=function(T,k){if(k!==void 0&&k.isCamera!==!0){console.error("THREE.WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(R===!0)return;if(T.matrixWorldAutoUpdate===!0&&T.updateMatrixWorld(),k.parent===null&&k.matrixWorldAutoUpdate===!0&&k.updateMatrixWorld(),q.enabled===!0&&q.isPresenting===!0&&(q.cameraAutoUpdate===!0&&q.updateCamera(k),k=q.getCamera()),T.isScene===!0&&T.onBeforeRender(M,T,k,P),u=tt.get(T,v.length),u.init(k),v.push(u),ye.multiplyMatrices(k.projectionMatrix,k.matrixWorldInverse),I.setFromProjectionMatrix(ye),ie=this.localClippingEnabled,z=K.init(this.clippingPlanes,ie),m=Pe.get(T,_.length),m.init(),_.push(m),q.enabled===!0&&q.isPresenting===!0){const de=M.xr.getDepthSensingMesh();de!==null&&_r(de,k,-1/0,M.sortObjects)}_r(T,k,0,M.sortObjects),m.finish(),M.sortObjects===!0&&m.sort(j,Z),pe=q.enabled===!1||q.isPresenting===!1||q.hasDepthSensing()===!1,pe&&ve.addToRenderList(m,T),this.info.render.frame++,z===!0&&K.beginShadows();const W=u.state.shadowsArray;se.render(W,T,k),z===!0&&K.endShadows(),this.info.autoReset===!0&&this.info.reset();const $=m.opaque,B=m.transmissive;if(u.setupLights(),k.isArrayCamera){const de=k.cameras;if(B.length>0)for(let Ce=0,De=de.length;Ce<De;Ce++){const Oe=de[Ce];fa($,B,T,Oe)}pe&&ve.render(T);for(let Ce=0,De=de.length;Ce<De;Ce++){const Oe=de[Ce];ha(m,T,Oe,Oe.viewport)}}else B.length>0&&fa($,B,T,k),pe&&ve.render(T),ha(m,T,k);P!==null&&(b.updateMultisampleRenderTarget(P),b.updateRenderTargetMipmap(P)),T.isScene===!0&&T.onAfterRender(M,T,k),Qe.resetDefaultState(),E=-1,S=null,v.pop(),v.length>0?(u=v[v.length-1],z===!0&&K.setGlobalState(M.clippingPlanes,u.state.camera)):u=null,_.pop(),_.length>0?m=_[_.length-1]:m=null};function _r(T,k,W,$){if(T.visible===!1)return;if(T.layers.test(k.layers)){if(T.isGroup)W=T.renderOrder;else if(T.isLOD)T.autoUpdate===!0&&T.update(k);else if(T.isLight)u.pushLight(T),T.castShadow&&u.pushShadow(T);else if(T.isSprite){if(!T.frustumCulled||I.intersectsSprite(T)){$&&te.setFromMatrixPosition(T.matrixWorld).applyMatrix4(ye);const Ce=ee.update(T),De=T.material;De.visible&&m.push(T,Ce,De,W,te.z,null)}}else if((T.isMesh||T.isLine||T.isPoints)&&(!T.frustumCulled||I.intersectsObject(T))){const Ce=ee.update(T),De=T.material;if($&&(T.boundingSphere!==void 0?(T.boundingSphere===null&&T.computeBoundingSphere(),te.copy(T.boundingSphere.center)):(Ce.boundingSphere===null&&Ce.computeBoundingSphere(),te.copy(Ce.boundingSphere.center)),te.applyMatrix4(T.matrixWorld).applyMatrix4(ye)),Array.isArray(De)){const Oe=Ce.groups;for(let Ye=0,qe=Oe.length;Ye<qe;Ye++){const Ge=Oe[Ye],st=De[Ge.materialIndex];st&&st.visible&&m.push(T,Ce,st,W,te.z,Ge)}}else De.visible&&m.push(T,Ce,De,W,te.z,null)}}const de=T.children;for(let Ce=0,De=de.length;Ce<De;Ce++)_r(de[Ce],k,W,$)}function ha(T,k,W,$){const B=T.opaque,de=T.transmissive,Ce=T.transparent;u.setupLightsView(W),z===!0&&K.setGlobalState(M.clippingPlanes,W),$&&Te.viewport(D.copy($)),B.length>0&&ce(B,k,W),de.length>0&&ce(de,k,W),Ce.length>0&&ce(Ce,k,W),Te.buffers.depth.setTest(!0),Te.buffers.depth.setMask(!0),Te.buffers.color.setMask(!0),Te.setPolygonOffset(!1)}function fa(T,k,W,$){if((W.isScene===!0?W.overrideMaterial:null)!==null)return;u.state.transmissionRenderTarget[$.id]===void 0&&(u.state.transmissionRenderTarget[$.id]=new Gr(1,1,{generateMipmaps:!0,type:ze.has("EXT_color_buffer_half_float")||ze.has("EXT_color_buffer_float")?oa:Ui,minFilter:Ir,samples:4,stencilBuffer:s,resolveDepthBuffer:!1,resolveStencilBuffer:!1,colorSpace:lt.workingColorSpace}));const de=u.state.transmissionRenderTarget[$.id],Ce=$.viewport||D;de.setSize(Ce.z,Ce.w);const De=M.getRenderTarget();M.setRenderTarget(de),M.getClearColor(U),Y=M.getClearAlpha(),Y<1&&M.setClearColor(16777215,.5),M.clear(),pe&&ve.render(W);const Oe=M.toneMapping;M.toneMapping=cr;const Ye=$.viewport;if($.viewport!==void 0&&($.viewport=void 0),u.setupLightsView($),z===!0&&K.setGlobalState(M.clippingPlanes,$),ce(T,W,$),b.updateMultisampleRenderTarget(de),b.updateRenderTargetMipmap(de),ze.has("WEBGL_multisampled_render_to_texture")===!1){let qe=!1;for(let Ge=0,st=k.length;Ge<st;Ge++){const ut=k[Ge],Nt=ut.object,Ct=ut.geometry,at=ut.material,We=ut.group;if(at.side===wi&&Nt.layers.test($.layers)){const jt=at.side;at.side=gn,at.needsUpdate=!0,ge(Nt,W,$,Ct,at,We),at.side=jt,at.needsUpdate=!0,qe=!0}}qe===!0&&(b.updateMultisampleRenderTarget(de),b.updateRenderTargetMipmap(de))}M.setRenderTarget(De),M.setClearColor(U,Y),Ye!==void 0&&($.viewport=Ye),M.toneMapping=Oe}function ce(T,k,W){const $=k.isScene===!0?k.overrideMaterial:null;for(let B=0,de=T.length;B<de;B++){const Ce=T[B],De=Ce.object,Oe=Ce.geometry,Ye=$===null?Ce.material:$,qe=Ce.group;De.layers.test(W.layers)&&ge(De,k,W,Oe,Ye,qe)}}function ge(T,k,W,$,B,de){T.onBeforeRender(M,k,W,$,B,de),T.modelViewMatrix.multiplyMatrices(W.matrixWorldInverse,T.matrixWorld),T.normalMatrix.getNormalMatrix(T.modelViewMatrix),B.onBeforeRender(M,k,W,$,T,de),B.transparent===!0&&B.side===wi&&B.forceSinglePass===!1?(B.side=gn,B.needsUpdate=!0,M.renderBufferDirect(W,k,$,B,T,de),B.side=hr,B.needsUpdate=!0,M.renderBufferDirect(W,k,$,B,T,de),B.side=wi):M.renderBufferDirect(W,k,$,B,T,de),T.onAfterRender(M,k,W,$,B,de)}function Be(T,k,W){k.isScene!==!0&&(k=me);const $=we.get(T),B=u.state.lights,de=u.state.shadowsArray,Ce=B.state.version,De=Ie.getParameters(T,B.state,de,k,W),Oe=Ie.getProgramCacheKey(De);let Ye=$.programs;$.environment=T.isMeshStandardMaterial?k.environment:null,$.fog=k.fog,$.envMap=(T.isMeshStandardMaterial?G:w).get(T.envMap||$.environment),$.envMapRotation=$.environment!==null&&T.envMap===null?k.environmentRotation:T.envMapRotation,Ye===void 0&&(T.addEventListener("dispose",Ke),Ye=new Map,$.programs=Ye);let qe=Ye.get(Oe);if(qe!==void 0){if($.currentProgram===qe&&$.lightsStateVersion===Ce)return rt(T,De),qe}else De.uniforms=Ie.getUniforms(T),T.onBeforeCompile(De,M),qe=Ie.acquireProgram(De,Oe),Ye.set(Oe,qe),$.uniforms=De.uniforms;const Ge=$.uniforms;return(!T.isShaderMaterial&&!T.isRawShaderMaterial||T.clipping===!0)&&(Ge.clippingPlanes=K.uniform),rt(T,De),$.needsLights=Yt(T),$.lightsStateVersion=Ce,$.needsLights&&(Ge.ambientLightColor.value=B.state.ambient,Ge.lightProbe.value=B.state.probe,Ge.directionalLights.value=B.state.directional,Ge.directionalLightShadows.value=B.state.directionalShadow,Ge.spotLights.value=B.state.spot,Ge.spotLightShadows.value=B.state.spotShadow,Ge.rectAreaLights.value=B.state.rectArea,Ge.ltc_1.value=B.state.rectAreaLTC1,Ge.ltc_2.value=B.state.rectAreaLTC2,Ge.pointLights.value=B.state.point,Ge.pointLightShadows.value=B.state.pointShadow,Ge.hemisphereLights.value=B.state.hemi,Ge.directionalShadowMap.value=B.state.directionalShadowMap,Ge.directionalShadowMatrix.value=B.state.directionalShadowMatrix,Ge.spotShadowMap.value=B.state.spotShadowMap,Ge.spotLightMatrix.value=B.state.spotLightMatrix,Ge.spotLightMap.value=B.state.spotLightMap,Ge.pointShadowMap.value=B.state.pointShadowMap,Ge.pointShadowMatrix.value=B.state.pointShadowMatrix),$.currentProgram=qe,$.uniformsList=null,qe}function Le(T){if(T.uniformsList===null){const k=T.currentProgram.getUniforms();T.uniformsList=wl.seqWithValue(k.seq,T.uniforms)}return T.uniformsList}function rt(T,k){const W=we.get(T);W.outputColorSpace=k.outputColorSpace,W.batching=k.batching,W.batchingColor=k.batchingColor,W.instancing=k.instancing,W.instancingColor=k.instancingColor,W.instancingMorph=k.instancingMorph,W.skinning=k.skinning,W.morphTargets=k.morphTargets,W.morphNormals=k.morphNormals,W.morphColors=k.morphColors,W.morphTargetsCount=k.morphTargetsCount,W.numClippingPlanes=k.numClippingPlanes,W.numIntersection=k.numClipIntersection,W.vertexAlphas=k.vertexAlphas,W.vertexTangents=k.vertexTangents,W.toneMapping=k.toneMapping}function ke(T,k,W,$,B){k.isScene!==!0&&(k=me),b.resetTextureUnits();const de=k.fog,Ce=$.isMeshStandardMaterial?k.environment:null,De=P===null?M.outputColorSpace:P.isXRRenderTarget===!0?P.texture.colorSpace:qs,Oe=($.isMeshStandardMaterial?G:w).get($.envMap||Ce),Ye=$.vertexColors===!0&&!!W.attributes.color&&W.attributes.color.itemSize===4,qe=!!W.attributes.tangent&&(!!$.normalMap||$.anisotropy>0),Ge=!!W.morphAttributes.position,st=!!W.morphAttributes.normal,ut=!!W.morphAttributes.color;let Nt=cr;$.toneMapped&&(P===null||P.isXRRenderTarget===!0)&&(Nt=M.toneMapping);const Ct=W.morphAttributes.position||W.morphAttributes.normal||W.morphAttributes.color,at=Ct!==void 0?Ct.length:0,We=we.get($),jt=u.state.lights;if(z===!0&&(ie===!0||T!==S)){const tn=T===S&&$.id===E;K.setState($,T,tn)}let dt=!1;$.version===We.__version?(We.needsLights&&We.lightsStateVersion!==jt.state.version||We.outputColorSpace!==De||B.isBatchedMesh&&We.batching===!1||!B.isBatchedMesh&&We.batching===!0||B.isBatchedMesh&&We.batchingColor===!0&&B.colorTexture===null||B.isBatchedMesh&&We.batchingColor===!1&&B.colorTexture!==null||B.isInstancedMesh&&We.instancing===!1||!B.isInstancedMesh&&We.instancing===!0||B.isSkinnedMesh&&We.skinning===!1||!B.isSkinnedMesh&&We.skinning===!0||B.isInstancedMesh&&We.instancingColor===!0&&B.instanceColor===null||B.isInstancedMesh&&We.instancingColor===!1&&B.instanceColor!==null||B.isInstancedMesh&&We.instancingMorph===!0&&B.morphTexture===null||B.isInstancedMesh&&We.instancingMorph===!1&&B.morphTexture!==null||We.envMap!==Oe||$.fog===!0&&We.fog!==de||We.numClippingPlanes!==void 0&&(We.numClippingPlanes!==K.numPlanes||We.numIntersection!==K.numIntersection)||We.vertexAlphas!==Ye||We.vertexTangents!==qe||We.morphTargets!==Ge||We.morphNormals!==st||We.morphColors!==ut||We.toneMapping!==Nt||We.morphTargetsCount!==at)&&(dt=!0):(dt=!0,We.__version=$.version);let Gn=We.currentProgram;dt===!0&&(Gn=Be($,k,B));let qr=!1,yn=!1,no=!1;const yt=Gn.getUniforms(),Ln=We.uniforms;if(Te.useProgram(Gn.program)&&(qr=!0,yn=!0,no=!0),$.id!==E&&(E=$.id,yn=!0),qr||S!==T){Te.buffers.depth.getReversed()?(le.copy(T.projectionMatrix),$S(le),YS(le),yt.setValue(L,"projectionMatrix",le)):yt.setValue(L,"projectionMatrix",T.projectionMatrix),yt.setValue(L,"viewMatrix",T.matrixWorldInverse);const ln=yt.map.cameraPosition;ln!==void 0&&ln.setValue(L,oe.setFromMatrixPosition(T.matrixWorld)),He.logarithmicDepthBuffer&&yt.setValue(L,"logDepthBufFC",2/(Math.log(T.far+1)/Math.LN2)),($.isMeshPhongMaterial||$.isMeshToonMaterial||$.isMeshLambertMaterial||$.isMeshBasicMaterial||$.isMeshStandardMaterial||$.isShaderMaterial)&&yt.setValue(L,"isOrthographic",T.isOrthographicCamera===!0),S!==T&&(S=T,yn=!0,no=!0)}if(B.isSkinnedMesh){yt.setOptional(L,B,"bindMatrix"),yt.setOptional(L,B,"bindMatrixInverse");const tn=B.skeleton;tn&&(tn.boneTexture===null&&tn.computeBoneTexture(),yt.setValue(L,"boneTexture",tn.boneTexture,b))}B.isBatchedMesh&&(yt.setOptional(L,B,"batchingTexture"),yt.setValue(L,"batchingTexture",B._matricesTexture,b),yt.setOptional(L,B,"batchingIdTexture"),yt.setValue(L,"batchingIdTexture",B._indirectTexture,b),yt.setOptional(L,B,"batchingColorTexture"),B._colorsTexture!==null&&yt.setValue(L,"batchingColorTexture",B._colorsTexture,b));const Nn=W.morphAttributes;if((Nn.position!==void 0||Nn.normal!==void 0||Nn.color!==void 0)&&Me.update(B,W,Gn),(yn||We.receiveShadow!==B.receiveShadow)&&(We.receiveShadow=B.receiveShadow,yt.setValue(L,"receiveShadow",B.receiveShadow)),$.isMeshGouraudMaterial&&$.envMap!==null&&(Ln.envMap.value=Oe,Ln.flipEnvMap.value=Oe.isCubeTexture&&Oe.isRenderTargetTexture===!1?-1:1),$.isMeshStandardMaterial&&$.envMap===null&&k.environment!==null&&(Ln.envMapIntensity.value=k.environmentIntensity),yn&&(yt.setValue(L,"toneMappingExposure",M.toneMappingExposure),We.needsLights&&At(Ln,no),de&&$.fog===!0&&Se.refreshFogUniforms(Ln,de),Se.refreshMaterialUniforms(Ln,$,N,J,u.state.transmissionRenderTarget[T.id]),wl.upload(L,Le(We),Ln,b)),$.isShaderMaterial&&$.uniformsNeedUpdate===!0&&(wl.upload(L,Le(We),Ln,b),$.uniformsNeedUpdate=!1),$.isSpriteMaterial&&yt.setValue(L,"center",B.center),yt.setValue(L,"modelViewMatrix",B.modelViewMatrix),yt.setValue(L,"normalMatrix",B.normalMatrix),yt.setValue(L,"modelMatrix",B.matrixWorld),$.isShaderMaterial||$.isRawShaderMaterial){const tn=$.uniformsGroups;for(let ln=0,Tc=tn.length;ln<Tc;ln++){const vr=tn[ln];F.update(vr,Gn),F.bind(vr,Gn)}}return Gn}function At(T,k){T.ambientLightColor.needsUpdate=k,T.lightProbe.needsUpdate=k,T.directionalLights.needsUpdate=k,T.directionalLightShadows.needsUpdate=k,T.pointLights.needsUpdate=k,T.pointLightShadows.needsUpdate=k,T.spotLights.needsUpdate=k,T.spotLightShadows.needsUpdate=k,T.rectAreaLights.needsUpdate=k,T.hemisphereLights.needsUpdate=k}function Yt(T){return T.isMeshLambertMaterial||T.isMeshToonMaterial||T.isMeshPhongMaterial||T.isMeshStandardMaterial||T.isShadowMaterial||T.isShaderMaterial&&T.lights===!0}this.getActiveCubeFace=function(){return C},this.getActiveMipmapLevel=function(){return A},this.getRenderTarget=function(){return P},this.setRenderTargetTextures=function(T,k,W){we.get(T.texture).__webglTexture=k,we.get(T.depthTexture).__webglTexture=W;const $=we.get(T);$.__hasExternalTextures=!0,$.__autoAllocateDepthBuffer=W===void 0,$.__autoAllocateDepthBuffer||ze.has("WEBGL_multisampled_render_to_texture")===!0&&(console.warn("THREE.WebGLRenderer: Render-to-texture extension was disabled because an external texture was provided"),$.__useRenderToTexture=!1)},this.setRenderTargetFramebuffer=function(T,k){const W=we.get(T);W.__webglFramebuffer=k,W.__useDefaultFramebuffer=k===void 0},this.setRenderTarget=function(T,k=0,W=0){P=T,C=k,A=W;let $=!0,B=null,de=!1,Ce=!1;if(T){const Oe=we.get(T);if(Oe.__useDefaultFramebuffer!==void 0)Te.bindFramebuffer(L.FRAMEBUFFER,null),$=!1;else if(Oe.__webglFramebuffer===void 0)b.setupRenderTarget(T);else if(Oe.__hasExternalTextures)b.rebindTextures(T,we.get(T.texture).__webglTexture,we.get(T.depthTexture).__webglTexture);else if(T.depthBuffer){const Ge=T.depthTexture;if(Oe.__boundDepthTexture!==Ge){if(Ge!==null&&we.has(Ge)&&(T.width!==Ge.image.width||T.height!==Ge.image.height))throw new Error("WebGLRenderTarget: Attached DepthTexture is initialized to the incorrect size.");b.setupDepthRenderbuffer(T)}}const Ye=T.texture;(Ye.isData3DTexture||Ye.isDataArrayTexture||Ye.isCompressedArrayTexture)&&(Ce=!0);const qe=we.get(T).__webglFramebuffer;T.isWebGLCubeRenderTarget?(Array.isArray(qe[k])?B=qe[k][W]:B=qe[k],de=!0):T.samples>0&&b.useMultisampledRTT(T)===!1?B=we.get(T).__webglMultisampledFramebuffer:Array.isArray(qe)?B=qe[W]:B=qe,D.copy(T.viewport),X.copy(T.scissor),H=T.scissorTest}else D.copy(fe).multiplyScalar(N).floor(),X.copy(_e).multiplyScalar(N).floor(),H=Re;if(Te.bindFramebuffer(L.FRAMEBUFFER,B)&&$&&Te.drawBuffers(T,B),Te.viewport(D),Te.scissor(X),Te.setScissorTest(H),de){const Oe=we.get(T.texture);L.framebufferTexture2D(L.FRAMEBUFFER,L.COLOR_ATTACHMENT0,L.TEXTURE_CUBE_MAP_POSITIVE_X+k,Oe.__webglTexture,W)}else if(Ce){const Oe=we.get(T.texture),Ye=k||0;L.framebufferTextureLayer(L.FRAMEBUFFER,L.COLOR_ATTACHMENT0,Oe.__webglTexture,W||0,Ye)}E=-1},this.readRenderTargetPixels=function(T,k,W,$,B,de,Ce){if(!(T&&T.isWebGLRenderTarget)){console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let De=we.get(T).__webglFramebuffer;if(T.isWebGLCubeRenderTarget&&Ce!==void 0&&(De=De[Ce]),De){Te.bindFramebuffer(L.FRAMEBUFFER,De);try{const Oe=T.texture,Ye=Oe.format,qe=Oe.type;if(!He.textureFormatReadable(Ye)){console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if(!He.textureTypeReadable(qe)){console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}k>=0&&k<=T.width-$&&W>=0&&W<=T.height-B&&L.readPixels(k,W,$,B,Ve.convert(Ye),Ve.convert(qe),de)}finally{const Oe=P!==null?we.get(P).__webglFramebuffer:null;Te.bindFramebuffer(L.FRAMEBUFFER,Oe)}}},this.readRenderTargetPixelsAsync=async function(T,k,W,$,B,de,Ce){if(!(T&&T.isWebGLRenderTarget))throw new Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let De=we.get(T).__webglFramebuffer;if(T.isWebGLCubeRenderTarget&&Ce!==void 0&&(De=De[Ce]),De){const Oe=T.texture,Ye=Oe.format,qe=Oe.type;if(!He.textureFormatReadable(Ye))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if(!He.textureTypeReadable(qe))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");if(k>=0&&k<=T.width-$&&W>=0&&W<=T.height-B){Te.bindFramebuffer(L.FRAMEBUFFER,De);const Ge=L.createBuffer();L.bindBuffer(L.PIXEL_PACK_BUFFER,Ge),L.bufferData(L.PIXEL_PACK_BUFFER,de.byteLength,L.STREAM_READ),L.readPixels(k,W,$,B,Ve.convert(Ye),Ve.convert(qe),0);const st=P!==null?we.get(P).__webglFramebuffer:null;Te.bindFramebuffer(L.FRAMEBUFFER,st);const ut=L.fenceSync(L.SYNC_GPU_COMMANDS_COMPLETE,0);return L.flush(),await XS(L,ut,4),L.bindBuffer(L.PIXEL_PACK_BUFFER,Ge),L.getBufferSubData(L.PIXEL_PACK_BUFFER,0,de),L.deleteBuffer(Ge),L.deleteSync(ut),de}else throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")}},this.copyFramebufferToTexture=function(T,k=null,W=0){T.isTexture!==!0&&(hs("WebGLRenderer: copyFramebufferToTexture function signature has changed."),k=arguments[0]||null,T=arguments[1]);const $=Math.pow(2,-W),B=Math.floor(T.image.width*$),de=Math.floor(T.image.height*$),Ce=k!==null?k.x:0,De=k!==null?k.y:0;b.setTexture2D(T,0),L.copyTexSubImage2D(L.TEXTURE_2D,W,0,0,Ce,De,B,de),Te.unbindTexture()};const Yr=L.createFramebuffer(),pi=L.createFramebuffer();this.copyTextureToTexture=function(T,k,W=null,$=null,B=0,de=null){T.isTexture!==!0&&(hs("WebGLRenderer: copyTextureToTexture function signature has changed."),$=arguments[0]||null,T=arguments[1],k=arguments[2],de=arguments[3]||0,W=null),de===null&&(B!==0?(hs("WebGLRenderer: copyTextureToTexture function signature has changed to support src and dst mipmap levels."),de=B,B=0):de=0);let Ce,De,Oe,Ye,qe,Ge,st,ut,Nt;const Ct=T.isCompressedTexture?T.mipmaps[de]:T.image;if(W!==null)Ce=W.max.x-W.min.x,De=W.max.y-W.min.y,Oe=W.isBox3?W.max.z-W.min.z:1,Ye=W.min.x,qe=W.min.y,Ge=W.isBox3?W.min.z:0;else{const Nn=Math.pow(2,-B);Ce=Math.floor(Ct.width*Nn),De=Math.floor(Ct.height*Nn),T.isDataArrayTexture?Oe=Ct.depth:T.isData3DTexture?Oe=Math.floor(Ct.depth*Nn):Oe=1,Ye=0,qe=0,Ge=0}$!==null?(st=$.x,ut=$.y,Nt=$.z):(st=0,ut=0,Nt=0);const at=Ve.convert(k.format),We=Ve.convert(k.type);let jt;k.isData3DTexture?(b.setTexture3D(k,0),jt=L.TEXTURE_3D):k.isDataArrayTexture||k.isCompressedArrayTexture?(b.setTexture2DArray(k,0),jt=L.TEXTURE_2D_ARRAY):(b.setTexture2D(k,0),jt=L.TEXTURE_2D),L.pixelStorei(L.UNPACK_FLIP_Y_WEBGL,k.flipY),L.pixelStorei(L.UNPACK_PREMULTIPLY_ALPHA_WEBGL,k.premultiplyAlpha),L.pixelStorei(L.UNPACK_ALIGNMENT,k.unpackAlignment);const dt=L.getParameter(L.UNPACK_ROW_LENGTH),Gn=L.getParameter(L.UNPACK_IMAGE_HEIGHT),qr=L.getParameter(L.UNPACK_SKIP_PIXELS),yn=L.getParameter(L.UNPACK_SKIP_ROWS),no=L.getParameter(L.UNPACK_SKIP_IMAGES);L.pixelStorei(L.UNPACK_ROW_LENGTH,Ct.width),L.pixelStorei(L.UNPACK_IMAGE_HEIGHT,Ct.height),L.pixelStorei(L.UNPACK_SKIP_PIXELS,Ye),L.pixelStorei(L.UNPACK_SKIP_ROWS,qe),L.pixelStorei(L.UNPACK_SKIP_IMAGES,Ge);const yt=T.isDataArrayTexture||T.isData3DTexture,Ln=k.isDataArrayTexture||k.isData3DTexture;if(T.isDepthTexture){const Nn=we.get(T),tn=we.get(k),ln=we.get(Nn.__renderTarget),Tc=we.get(tn.__renderTarget);Te.bindFramebuffer(L.READ_FRAMEBUFFER,ln.__webglFramebuffer),Te.bindFramebuffer(L.DRAW_FRAMEBUFFER,Tc.__webglFramebuffer);for(let vr=0;vr<Oe;vr++)yt&&(L.framebufferTextureLayer(L.READ_FRAMEBUFFER,L.COLOR_ATTACHMENT0,we.get(T).__webglTexture,B,Ge+vr),L.framebufferTextureLayer(L.DRAW_FRAMEBUFFER,L.COLOR_ATTACHMENT0,we.get(k).__webglTexture,de,Nt+vr)),L.blitFramebuffer(Ye,qe,Ce,De,st,ut,Ce,De,L.DEPTH_BUFFER_BIT,L.NEAREST);Te.bindFramebuffer(L.READ_FRAMEBUFFER,null),Te.bindFramebuffer(L.DRAW_FRAMEBUFFER,null)}else if(B!==0||T.isRenderTargetTexture||we.has(T)){const Nn=we.get(T),tn=we.get(k);Te.bindFramebuffer(L.READ_FRAMEBUFFER,Yr),Te.bindFramebuffer(L.DRAW_FRAMEBUFFER,pi);for(let ln=0;ln<Oe;ln++)yt?L.framebufferTextureLayer(L.READ_FRAMEBUFFER,L.COLOR_ATTACHMENT0,Nn.__webglTexture,B,Ge+ln):L.framebufferTexture2D(L.READ_FRAMEBUFFER,L.COLOR_ATTACHMENT0,L.TEXTURE_2D,Nn.__webglTexture,B),Ln?L.framebufferTextureLayer(L.DRAW_FRAMEBUFFER,L.COLOR_ATTACHMENT0,tn.__webglTexture,de,Nt+ln):L.framebufferTexture2D(L.DRAW_FRAMEBUFFER,L.COLOR_ATTACHMENT0,L.TEXTURE_2D,tn.__webglTexture,de),B!==0?L.blitFramebuffer(Ye,qe,Ce,De,st,ut,Ce,De,L.COLOR_BUFFER_BIT,L.NEAREST):Ln?L.copyTexSubImage3D(jt,de,st,ut,Nt+ln,Ye,qe,Ce,De):L.copyTexSubImage2D(jt,de,st,ut,Ye,qe,Ce,De);Te.bindFramebuffer(L.READ_FRAMEBUFFER,null),Te.bindFramebuffer(L.DRAW_FRAMEBUFFER,null)}else Ln?T.isDataTexture||T.isData3DTexture?L.texSubImage3D(jt,de,st,ut,Nt,Ce,De,Oe,at,We,Ct.data):k.isCompressedArrayTexture?L.compressedTexSubImage3D(jt,de,st,ut,Nt,Ce,De,Oe,at,Ct.data):L.texSubImage3D(jt,de,st,ut,Nt,Ce,De,Oe,at,We,Ct):T.isDataTexture?L.texSubImage2D(L.TEXTURE_2D,de,st,ut,Ce,De,at,We,Ct.data):T.isCompressedTexture?L.compressedTexSubImage2D(L.TEXTURE_2D,de,st,ut,Ct.width,Ct.height,at,Ct.data):L.texSubImage2D(L.TEXTURE_2D,de,st,ut,Ce,De,at,We,Ct);L.pixelStorei(L.UNPACK_ROW_LENGTH,dt),L.pixelStorei(L.UNPACK_IMAGE_HEIGHT,Gn),L.pixelStorei(L.UNPACK_SKIP_PIXELS,qr),L.pixelStorei(L.UNPACK_SKIP_ROWS,yn),L.pixelStorei(L.UNPACK_SKIP_IMAGES,no),de===0&&k.generateMipmaps&&L.generateMipmap(jt),Te.unbindTexture()},this.copyTextureToTexture3D=function(T,k,W=null,$=null,B=0){return T.isTexture!==!0&&(hs("WebGLRenderer: copyTextureToTexture3D function signature has changed."),W=arguments[0]||null,$=arguments[1]||null,T=arguments[2],k=arguments[3],B=arguments[4]||0),hs('WebGLRenderer: copyTextureToTexture3D function has been deprecated. Use "copyTextureToTexture" instead.'),this.copyTextureToTexture(T,k,W,$,B)},this.initRenderTarget=function(T){we.get(T).__webglFramebuffer===void 0&&b.setupRenderTarget(T)},this.initTexture=function(T){T.isCubeTexture?b.setTextureCube(T,0):T.isData3DTexture?b.setTexture3D(T,0):T.isDataArrayTexture||T.isCompressedArrayTexture?b.setTexture2DArray(T,0):b.setTexture2D(T,0),Te.unbindTexture()},this.resetState=function(){C=0,A=0,P=null,Te.reset(),Qe.reset()},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return bi}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(e){this._outputColorSpace=e;const n=this.getContext();n.drawingBufferColorspace=lt._getDrawingBufferColorSpace(e),n.unpackColorSpace=lt._getUnpackColorSpace()}}const qm={type:"change"},Nf={type:"start"},r0={type:"end"},il=new Mc,Km=new Yi,AA=Math.cos(70*jS.DEG2RAD),Ut=new O,un=2*Math.PI,pt={NONE:-1,ROTATE:0,DOLLY:1,PAN:2,TOUCH_ROTATE:3,TOUCH_PAN:4,TOUCH_DOLLY_PAN:5,TOUCH_DOLLY_ROTATE:6},Fu=1e-6;class CA extends VM{constructor(e,n=null){super(e,n),this.state=pt.NONE,this.enabled=!0,this.target=new O,this.cursor=new O,this.minDistance=0,this.maxDistance=1/0,this.minZoom=0,this.maxZoom=1/0,this.minTargetRadius=0,this.maxTargetRadius=1/0,this.minPolarAngle=0,this.maxPolarAngle=Math.PI,this.minAzimuthAngle=-1/0,this.maxAzimuthAngle=1/0,this.enableDamping=!1,this.dampingFactor=.05,this.enableZoom=!0,this.zoomSpeed=1,this.enableRotate=!0,this.rotateSpeed=1,this.enablePan=!0,this.panSpeed=1,this.screenSpacePanning=!0,this.keyPanSpeed=7,this.zoomToCursor=!1,this.autoRotate=!1,this.autoRotateSpeed=2,this.keys={LEFT:"ArrowLeft",UP:"ArrowUp",RIGHT:"ArrowRight",BOTTOM:"ArrowDown"},this.mouseButtons={LEFT:Ds.ROTATE,MIDDLE:Ds.DOLLY,RIGHT:Ds.PAN},this.touches={ONE:Ts.ROTATE,TWO:Ts.DOLLY_PAN},this.target0=this.target.clone(),this.position0=this.object.position.clone(),this.zoom0=this.object.zoom,this._domElementKeyEvents=null,this._lastPosition=new O,this._lastQuaternion=new jr,this._lastTargetPosition=new O,this._quat=new jr().setFromUnitVectors(e.up,new O(0,1,0)),this._quatInverse=this._quat.clone().invert(),this._spherical=new Em,this._sphericalDelta=new Em,this._scale=1,this._panOffset=new O,this._rotateStart=new Fe,this._rotateEnd=new Fe,this._rotateDelta=new Fe,this._panStart=new Fe,this._panEnd=new Fe,this._panDelta=new Fe,this._dollyStart=new Fe,this._dollyEnd=new Fe,this._dollyDelta=new Fe,this._dollyDirection=new O,this._mouse=new Fe,this._performCursorZoom=!1,this._pointers=[],this._pointerPositions={},this._controlActive=!1,this._onPointerMove=RA.bind(this),this._onPointerDown=bA.bind(this),this._onPointerUp=PA.bind(this),this._onContextMenu=FA.bind(this),this._onMouseWheel=DA.bind(this),this._onKeyDown=IA.bind(this),this._onTouchStart=UA.bind(this),this._onTouchMove=OA.bind(this),this._onMouseDown=LA.bind(this),this._onMouseMove=NA.bind(this),this._interceptControlDown=kA.bind(this),this._interceptControlUp=BA.bind(this),this.domElement!==null&&this.connect(),this.update()}connect(){this.domElement.addEventListener("pointerdown",this._onPointerDown),this.domElement.addEventListener("pointercancel",this._onPointerUp),this.domElement.addEventListener("contextmenu",this._onContextMenu),this.domElement.addEventListener("wheel",this._onMouseWheel,{passive:!1}),this.domElement.getRootNode().addEventListener("keydown",this._interceptControlDown,{passive:!0,capture:!0}),this.domElement.style.touchAction="none"}disconnect(){this.domElement.removeEventListener("pointerdown",this._onPointerDown),this.domElement.removeEventListener("pointermove",this._onPointerMove),this.domElement.removeEventListener("pointerup",this._onPointerUp),this.domElement.removeEventListener("pointercancel",this._onPointerUp),this.domElement.removeEventListener("wheel",this._onMouseWheel),this.domElement.removeEventListener("contextmenu",this._onContextMenu),this.stopListenToKeyEvents(),this.domElement.getRootNode().removeEventListener("keydown",this._interceptControlDown,{capture:!0}),this.domElement.style.touchAction="auto"}dispose(){this.disconnect()}getPolarAngle(){return this._spherical.phi}getAzimuthalAngle(){return this._spherical.theta}getDistance(){return this.object.position.distanceTo(this.target)}listenToKeyEvents(e){e.addEventListener("keydown",this._onKeyDown),this._domElementKeyEvents=e}stopListenToKeyEvents(){this._domElementKeyEvents!==null&&(this._domElementKeyEvents.removeEventListener("keydown",this._onKeyDown),this._domElementKeyEvents=null)}saveState(){this.target0.copy(this.target),this.position0.copy(this.object.position),this.zoom0=this.object.zoom}reset(){this.target.copy(this.target0),this.object.position.copy(this.position0),this.object.zoom=this.zoom0,this.object.updateProjectionMatrix(),this.dispatchEvent(qm),this.update(),this.state=pt.NONE}update(e=null){const n=this.object.position;Ut.copy(n).sub(this.target),Ut.applyQuaternion(this._quat),this._spherical.setFromVector3(Ut),this.autoRotate&&this.state===pt.NONE&&this._rotateLeft(this._getAutoRotationAngle(e)),this.enableDamping?(this._spherical.theta+=this._sphericalDelta.theta*this.dampingFactor,this._spherical.phi+=this._sphericalDelta.phi*this.dampingFactor):(this._spherical.theta+=this._sphericalDelta.theta,this._spherical.phi+=this._sphericalDelta.phi);let i=this.minAzimuthAngle,r=this.maxAzimuthAngle;isFinite(i)&&isFinite(r)&&(i<-Math.PI?i+=un:i>Math.PI&&(i-=un),r<-Math.PI?r+=un:r>Math.PI&&(r-=un),i<=r?this._spherical.theta=Math.max(i,Math.min(r,this._spherical.theta)):this._spherical.theta=this._spherical.theta>(i+r)/2?Math.max(i,this._spherical.theta):Math.min(r,this._spherical.theta)),this._spherical.phi=Math.max(this.minPolarAngle,Math.min(this.maxPolarAngle,this._spherical.phi)),this._spherical.makeSafe(),this.enableDamping===!0?this.target.addScaledVector(this._panOffset,this.dampingFactor):this.target.add(this._panOffset),this.target.sub(this.cursor),this.target.clampLength(this.minTargetRadius,this.maxTargetRadius),this.target.add(this.cursor);let s=!1;if(this.zoomToCursor&&this._performCursorZoom||this.object.isOrthographicCamera)this._spherical.radius=this._clampDistance(this._spherical.radius);else{const o=this._spherical.radius;this._spherical.radius=this._clampDistance(this._spherical.radius*this._scale),s=o!=this._spherical.radius}if(Ut.setFromSpherical(this._spherical),Ut.applyQuaternion(this._quatInverse),n.copy(this.target).add(Ut),this.object.lookAt(this.target),this.enableDamping===!0?(this._sphericalDelta.theta*=1-this.dampingFactor,this._sphericalDelta.phi*=1-this.dampingFactor,this._panOffset.multiplyScalar(1-this.dampingFactor)):(this._sphericalDelta.set(0,0,0),this._panOffset.set(0,0,0)),this.zoomToCursor&&this._performCursorZoom){let o=null;if(this.object.isPerspectiveCamera){const a=Ut.length();o=this._clampDistance(a*this._scale);const l=a-o;this.object.position.addScaledVector(this._dollyDirection,l),this.object.updateMatrixWorld(),s=!!l}else if(this.object.isOrthographicCamera){const a=new O(this._mouse.x,this._mouse.y,0);a.unproject(this.object);const l=this.object.zoom;this.object.zoom=Math.max(this.minZoom,Math.min(this.maxZoom,this.object.zoom/this._scale)),this.object.updateProjectionMatrix(),s=l!==this.object.zoom;const c=new O(this._mouse.x,this._mouse.y,0);c.unproject(this.object),this.object.position.sub(c).add(a),this.object.updateMatrixWorld(),o=Ut.length()}else console.warn("WARNING: OrbitControls.js encountered an unknown camera type - zoom to cursor disabled."),this.zoomToCursor=!1;o!==null&&(this.screenSpacePanning?this.target.set(0,0,-1).transformDirection(this.object.matrix).multiplyScalar(o).add(this.object.position):(il.origin.copy(this.object.position),il.direction.set(0,0,-1).transformDirection(this.object.matrix),Math.abs(this.object.up.dot(il.direction))<AA?this.object.lookAt(this.target):(Km.setFromNormalAndCoplanarPoint(this.object.up,this.target),il.intersectPlane(Km,this.target))))}else if(this.object.isOrthographicCamera){const o=this.object.zoom;this.object.zoom=Math.max(this.minZoom,Math.min(this.maxZoom,this.object.zoom/this._scale)),o!==this.object.zoom&&(this.object.updateProjectionMatrix(),s=!0)}return this._scale=1,this._performCursorZoom=!1,s||this._lastPosition.distanceToSquared(this.object.position)>Fu||8*(1-this._lastQuaternion.dot(this.object.quaternion))>Fu||this._lastTargetPosition.distanceToSquared(this.target)>Fu?(this.dispatchEvent(qm),this._lastPosition.copy(this.object.position),this._lastQuaternion.copy(this.object.quaternion),this._lastTargetPosition.copy(this.target),!0):!1}_getAutoRotationAngle(e){return e!==null?un/60*this.autoRotateSpeed*e:un/60/60*this.autoRotateSpeed}_getZoomScale(e){const n=Math.abs(e*.01);return Math.pow(.95,this.zoomSpeed*n)}_rotateLeft(e){this._sphericalDelta.theta-=e}_rotateUp(e){this._sphericalDelta.phi-=e}_panLeft(e,n){Ut.setFromMatrixColumn(n,0),Ut.multiplyScalar(-e),this._panOffset.add(Ut)}_panUp(e,n){this.screenSpacePanning===!0?Ut.setFromMatrixColumn(n,1):(Ut.setFromMatrixColumn(n,0),Ut.crossVectors(this.object.up,Ut)),Ut.multiplyScalar(e),this._panOffset.add(Ut)}_pan(e,n){const i=this.domElement;if(this.object.isPerspectiveCamera){const r=this.object.position;Ut.copy(r).sub(this.target);let s=Ut.length();s*=Math.tan(this.object.fov/2*Math.PI/180),this._panLeft(2*e*s/i.clientHeight,this.object.matrix),this._panUp(2*n*s/i.clientHeight,this.object.matrix)}else this.object.isOrthographicCamera?(this._panLeft(e*(this.object.right-this.object.left)/this.object.zoom/i.clientWidth,this.object.matrix),this._panUp(n*(this.object.top-this.object.bottom)/this.object.zoom/i.clientHeight,this.object.matrix)):(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - pan disabled."),this.enablePan=!1)}_dollyOut(e){this.object.isPerspectiveCamera||this.object.isOrthographicCamera?this._scale/=e:(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled."),this.enableZoom=!1)}_dollyIn(e){this.object.isPerspectiveCamera||this.object.isOrthographicCamera?this._scale*=e:(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled."),this.enableZoom=!1)}_updateZoomParameters(e,n){if(!this.zoomToCursor)return;this._performCursorZoom=!0;const i=this.domElement.getBoundingClientRect(),r=e-i.left,s=n-i.top,o=i.width,a=i.height;this._mouse.x=r/o*2-1,this._mouse.y=-(s/a)*2+1,this._dollyDirection.set(this._mouse.x,this._mouse.y,1).unproject(this.object).sub(this.object.position).normalize()}_clampDistance(e){return Math.max(this.minDistance,Math.min(this.maxDistance,e))}_handleMouseDownRotate(e){this._rotateStart.set(e.clientX,e.clientY)}_handleMouseDownDolly(e){this._updateZoomParameters(e.clientX,e.clientX),this._dollyStart.set(e.clientX,e.clientY)}_handleMouseDownPan(e){this._panStart.set(e.clientX,e.clientY)}_handleMouseMoveRotate(e){this._rotateEnd.set(e.clientX,e.clientY),this._rotateDelta.subVectors(this._rotateEnd,this._rotateStart).multiplyScalar(this.rotateSpeed);const n=this.domElement;this._rotateLeft(un*this._rotateDelta.x/n.clientHeight),this._rotateUp(un*this._rotateDelta.y/n.clientHeight),this._rotateStart.copy(this._rotateEnd),this.update()}_handleMouseMoveDolly(e){this._dollyEnd.set(e.clientX,e.clientY),this._dollyDelta.subVectors(this._dollyEnd,this._dollyStart),this._dollyDelta.y>0?this._dollyOut(this._getZoomScale(this._dollyDelta.y)):this._dollyDelta.y<0&&this._dollyIn(this._getZoomScale(this._dollyDelta.y)),this._dollyStart.copy(this._dollyEnd),this.update()}_handleMouseMovePan(e){this._panEnd.set(e.clientX,e.clientY),this._panDelta.subVectors(this._panEnd,this._panStart).multiplyScalar(this.panSpeed),this._pan(this._panDelta.x,this._panDelta.y),this._panStart.copy(this._panEnd),this.update()}_handleMouseWheel(e){this._updateZoomParameters(e.clientX,e.clientY),e.deltaY<0?this._dollyIn(this._getZoomScale(e.deltaY)):e.deltaY>0&&this._dollyOut(this._getZoomScale(e.deltaY)),this.update()}_handleKeyDown(e){let n=!1;switch(e.code){case this.keys.UP:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateUp(un*this.rotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(0,this.keyPanSpeed),n=!0;break;case this.keys.BOTTOM:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateUp(-un*this.rotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(0,-this.keyPanSpeed),n=!0;break;case this.keys.LEFT:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateLeft(un*this.rotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(this.keyPanSpeed,0),n=!0;break;case this.keys.RIGHT:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateLeft(-un*this.rotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(-this.keyPanSpeed,0),n=!0;break}n&&(e.preventDefault(),this.update())}_handleTouchStartRotate(e){if(this._pointers.length===1)this._rotateStart.set(e.pageX,e.pageY);else{const n=this._getSecondPointerPosition(e),i=.5*(e.pageX+n.x),r=.5*(e.pageY+n.y);this._rotateStart.set(i,r)}}_handleTouchStartPan(e){if(this._pointers.length===1)this._panStart.set(e.pageX,e.pageY);else{const n=this._getSecondPointerPosition(e),i=.5*(e.pageX+n.x),r=.5*(e.pageY+n.y);this._panStart.set(i,r)}}_handleTouchStartDolly(e){const n=this._getSecondPointerPosition(e),i=e.pageX-n.x,r=e.pageY-n.y,s=Math.sqrt(i*i+r*r);this._dollyStart.set(0,s)}_handleTouchStartDollyPan(e){this.enableZoom&&this._handleTouchStartDolly(e),this.enablePan&&this._handleTouchStartPan(e)}_handleTouchStartDollyRotate(e){this.enableZoom&&this._handleTouchStartDolly(e),this.enableRotate&&this._handleTouchStartRotate(e)}_handleTouchMoveRotate(e){if(this._pointers.length==1)this._rotateEnd.set(e.pageX,e.pageY);else{const i=this._getSecondPointerPosition(e),r=.5*(e.pageX+i.x),s=.5*(e.pageY+i.y);this._rotateEnd.set(r,s)}this._rotateDelta.subVectors(this._rotateEnd,this._rotateStart).multiplyScalar(this.rotateSpeed);const n=this.domElement;this._rotateLeft(un*this._rotateDelta.x/n.clientHeight),this._rotateUp(un*this._rotateDelta.y/n.clientHeight),this._rotateStart.copy(this._rotateEnd)}_handleTouchMovePan(e){if(this._pointers.length===1)this._panEnd.set(e.pageX,e.pageY);else{const n=this._getSecondPointerPosition(e),i=.5*(e.pageX+n.x),r=.5*(e.pageY+n.y);this._panEnd.set(i,r)}this._panDelta.subVectors(this._panEnd,this._panStart).multiplyScalar(this.panSpeed),this._pan(this._panDelta.x,this._panDelta.y),this._panStart.copy(this._panEnd)}_handleTouchMoveDolly(e){const n=this._getSecondPointerPosition(e),i=e.pageX-n.x,r=e.pageY-n.y,s=Math.sqrt(i*i+r*r);this._dollyEnd.set(0,s),this._dollyDelta.set(0,Math.pow(this._dollyEnd.y/this._dollyStart.y,this.zoomSpeed)),this._dollyOut(this._dollyDelta.y),this._dollyStart.copy(this._dollyEnd);const o=(e.pageX+n.x)*.5,a=(e.pageY+n.y)*.5;this._updateZoomParameters(o,a)}_handleTouchMoveDollyPan(e){this.enableZoom&&this._handleTouchMoveDolly(e),this.enablePan&&this._handleTouchMovePan(e)}_handleTouchMoveDollyRotate(e){this.enableZoom&&this._handleTouchMoveDolly(e),this.enableRotate&&this._handleTouchMoveRotate(e)}_addPointer(e){this._pointers.push(e.pointerId)}_removePointer(e){delete this._pointerPositions[e.pointerId];for(let n=0;n<this._pointers.length;n++)if(this._pointers[n]==e.pointerId){this._pointers.splice(n,1);return}}_isTrackingPointer(e){for(let n=0;n<this._pointers.length;n++)if(this._pointers[n]==e.pointerId)return!0;return!1}_trackPointer(e){let n=this._pointerPositions[e.pointerId];n===void 0&&(n=new Fe,this._pointerPositions[e.pointerId]=n),n.set(e.pageX,e.pageY)}_getSecondPointerPosition(e){const n=e.pointerId===this._pointers[0]?this._pointers[1]:this._pointers[0];return this._pointerPositions[n]}_customWheelEvent(e){const n=e.deltaMode,i={clientX:e.clientX,clientY:e.clientY,deltaY:e.deltaY};switch(n){case 1:i.deltaY*=16;break;case 2:i.deltaY*=100;break}return e.ctrlKey&&!this._controlActive&&(i.deltaY*=10),i}}function bA(t){this.enabled!==!1&&(this._pointers.length===0&&(this.domElement.setPointerCapture(t.pointerId),this.domElement.addEventListener("pointermove",this._onPointerMove),this.domElement.addEventListener("pointerup",this._onPointerUp)),!this._isTrackingPointer(t)&&(this._addPointer(t),t.pointerType==="touch"?this._onTouchStart(t):this._onMouseDown(t)))}function RA(t){this.enabled!==!1&&(t.pointerType==="touch"?this._onTouchMove(t):this._onMouseMove(t))}function PA(t){switch(this._removePointer(t),this._pointers.length){case 0:this.domElement.releasePointerCapture(t.pointerId),this.domElement.removeEventListener("pointermove",this._onPointerMove),this.domElement.removeEventListener("pointerup",this._onPointerUp),this.dispatchEvent(r0),this.state=pt.NONE;break;case 1:const e=this._pointers[0],n=this._pointerPositions[e];this._onTouchStart({pointerId:e,pageX:n.x,pageY:n.y});break}}function LA(t){let e;switch(t.button){case 0:e=this.mouseButtons.LEFT;break;case 1:e=this.mouseButtons.MIDDLE;break;case 2:e=this.mouseButtons.RIGHT;break;default:e=-1}switch(e){case Ds.DOLLY:if(this.enableZoom===!1)return;this._handleMouseDownDolly(t),this.state=pt.DOLLY;break;case Ds.ROTATE:if(t.ctrlKey||t.metaKey||t.shiftKey){if(this.enablePan===!1)return;this._handleMouseDownPan(t),this.state=pt.PAN}else{if(this.enableRotate===!1)return;this._handleMouseDownRotate(t),this.state=pt.ROTATE}break;case Ds.PAN:if(t.ctrlKey||t.metaKey||t.shiftKey){if(this.enableRotate===!1)return;this._handleMouseDownRotate(t),this.state=pt.ROTATE}else{if(this.enablePan===!1)return;this._handleMouseDownPan(t),this.state=pt.PAN}break;default:this.state=pt.NONE}this.state!==pt.NONE&&this.dispatchEvent(Nf)}function NA(t){switch(this.state){case pt.ROTATE:if(this.enableRotate===!1)return;this._handleMouseMoveRotate(t);break;case pt.DOLLY:if(this.enableZoom===!1)return;this._handleMouseMoveDolly(t);break;case pt.PAN:if(this.enablePan===!1)return;this._handleMouseMovePan(t);break}}function DA(t){this.enabled===!1||this.enableZoom===!1||this.state!==pt.NONE||(t.preventDefault(),this.dispatchEvent(Nf),this._handleMouseWheel(this._customWheelEvent(t)),this.dispatchEvent(r0))}function IA(t){this.enabled!==!1&&this._handleKeyDown(t)}function UA(t){switch(this._trackPointer(t),this._pointers.length){case 1:switch(this.touches.ONE){case Ts.ROTATE:if(this.enableRotate===!1)return;this._handleTouchStartRotate(t),this.state=pt.TOUCH_ROTATE;break;case Ts.PAN:if(this.enablePan===!1)return;this._handleTouchStartPan(t),this.state=pt.TOUCH_PAN;break;default:this.state=pt.NONE}break;case 2:switch(this.touches.TWO){case Ts.DOLLY_PAN:if(this.enableZoom===!1&&this.enablePan===!1)return;this._handleTouchStartDollyPan(t),this.state=pt.TOUCH_DOLLY_PAN;break;case Ts.DOLLY_ROTATE:if(this.enableZoom===!1&&this.enableRotate===!1)return;this._handleTouchStartDollyRotate(t),this.state=pt.TOUCH_DOLLY_ROTATE;break;default:this.state=pt.NONE}break;default:this.state=pt.NONE}this.state!==pt.NONE&&this.dispatchEvent(Nf)}function OA(t){switch(this._trackPointer(t),this.state){case pt.TOUCH_ROTATE:if(this.enableRotate===!1)return;this._handleTouchMoveRotate(t),this.update();break;case pt.TOUCH_PAN:if(this.enablePan===!1)return;this._handleTouchMovePan(t),this.update();break;case pt.TOUCH_DOLLY_PAN:if(this.enableZoom===!1&&this.enablePan===!1)return;this._handleTouchMoveDollyPan(t),this.update();break;case pt.TOUCH_DOLLY_ROTATE:if(this.enableZoom===!1&&this.enableRotate===!1)return;this._handleTouchMoveDollyRotate(t),this.update();break;default:this.state=pt.NONE}}function FA(t){this.enabled!==!1&&t.preventDefault()}function kA(t){t.key==="Control"&&(this._controlActive=!0,this.domElement.getRootNode().addEventListener("keyup",this._interceptControlUp,{passive:!0,capture:!0}))}function BA(t){t.key==="Control"&&(this._controlActive=!1,this.domElement.getRootNode().removeEventListener("keyup",this._interceptControlUp,{passive:!0,capture:!0}))}class ku extends kt{constructor(e=document.createElement("div")){super(),this.isCSS2DObject=!0,this.element=e,this.element.style.position="absolute",this.element.style.userSelect="none",this.element.setAttribute("draggable",!1),this.center=new Fe(.5,.5),this.addEventListener("removed",function(){this.traverse(function(n){n.element instanceof n.element.ownerDocument.defaultView.Element&&n.element.parentNode!==null&&n.element.remove()})})}copy(e,n){return super.copy(e,n),this.element=e.element.cloneNode(!0),this.center=e.center,this}}const ds=new O,Zm=new mt,Jm=new mt,Qm=new O,eg=new O;class zA{constructor(e={}){const n=this;let i,r,s,o;const a={objects:new WeakMap},l=e.element!==void 0?e.element:document.createElement("div");l.style.overflow="hidden",this.domElement=l,this.getSize=function(){return{width:i,height:r}},this.render=function(g,x){g.matrixWorldAutoUpdate===!0&&g.updateMatrixWorld(),x.parent===null&&x.matrixWorldAutoUpdate===!0&&x.updateMatrixWorld(),Zm.copy(x.matrixWorldInverse),Jm.multiplyMatrices(x.projectionMatrix,Zm),d(g,g,x),p(g)},this.setSize=function(g,x){i=g,r=x,s=i/2,o=r/2,l.style.width=g+"px",l.style.height=x+"px"};function c(g){g.isCSS2DObject&&(g.element.style.display="none");for(let x=0,m=g.children.length;x<m;x++)c(g.children[x])}function d(g,x,m){if(g.visible===!1){c(g);return}if(g.isCSS2DObject){ds.setFromMatrixPosition(g.matrixWorld),ds.applyMatrix4(Jm);const u=ds.z>=-1&&ds.z<=1&&g.layers.test(m.layers)===!0,_=g.element;_.style.display=u===!0?"":"none",u===!0&&(g.onBeforeRender(n,x,m),_.style.transform="translate("+-100*g.center.x+"%,"+-100*g.center.y+"%)translate("+(ds.x*s+s)+"px,"+(-ds.y*o+o)+"px)",_.parentNode!==l&&l.appendChild(_),g.onAfterRender(n,x,m));const v={distanceToCameraSquared:h(m,g)};a.objects.set(g,v)}for(let u=0,_=g.children.length;u<_;u++)d(g.children[u],x,m)}function h(g,x){return Qm.setFromMatrixPosition(g.matrixWorld),eg.setFromMatrixPosition(x.matrixWorld),Qm.distanceToSquared(eg)}function f(g){const x=[];return g.traverseVisible(function(m){m.isCSS2DObject&&x.push(m)}),x}function p(g){const x=f(g).sort(function(u,_){if(u.renderOrder!==_.renderOrder)return _.renderOrder-u.renderOrder;const v=a.objects.get(u).distanceToCameraSquared,M=a.objects.get(_).distanceToCameraSquared;return v-M}),m=x.length;for(let u=0,_=x.length;u<_;u++)x[u].element.style.zIndex=m-u}}}const Yn={metal:4346717,empty:12371146,hover:11512300,pending:10262e3,bound:5921496,danger:10693933,bond:4013480,guide:14278370},HA=t=>({1:"mono",2:"bi",3:"tri",4:"tetra"})[t]||`${t}`,VA=(t,e=20)=>t.length>e?t.slice(0,e-1)+"…":t,Bu=(t,e)=>t<e?`${t},${e}`:`${e},${t}`,tg=t=>({2:"bidentate",3:"tridentate",4:"tetradentate"})[t]||`${t}-dentate`,GA=t=>t.length===1?`site ${t[0]}`:`sites ${t.slice(0,-1).join(", ")} and ${t[t.length-1]}`,ic={O:"#c65a2e",N:"#2f6fd0",S:"#b8860b",P:"#d07a1f",Cl:"#1f9e8a",Br:"#8a5a2b",I:"#7a3fb0",F:"#2f9e6a",C:"#8a929b"};ic.η=ic.C;const wh=t=>ic[t]||"#5a5ad8";function jA(t){const e=[1,3,5].map(r=>parseInt(t.slice(r,r+2),16)/255).map(r=>r<=.04045?r/12.92:((r+.055)/1.055)**2.4),n=.2126*e[0]+.7152*e[1]+.0722*e[2];return 1.05/(n+.05)>=(n+.05)/(.0118+.05)?"#fff":"#0e1b24"}function WA(t,e,n,i){if(!t||!t.atoms||!t.atoms.length)return null;const r=t.atoms,s=t.bonds||[],o=r.map(A=>A.x),a=r.map(A=>A.y),l=Math.min(...o),c=Math.max(...o),d=Math.min(...a),h=Math.max(...a),f=1.1,p=12,g=(c-l+2*f)*p,x=(h-d+2*f)*p,m=A=>((A-l+f)*p).toFixed(1),u=A=>((h-A+f)*p).toFixed(1),_=new Set(e||[]),v=n||{};let M="";for(const A of s){const P=r[A.a],E=r[A.b];M+=`<line x1="${m(P.x)}" y1="${u(P.y)}" x2="${m(E.x)}" y2="${u(E.y)}" stroke="currentColor" stroke-width="${A.order>=2?2:1.2}" stroke-opacity="0.7"/>`}for(const A of r)if(_.has(A.idx)){const E=i?ic.C:wh(A.symbol),S=i?5.5:7;M+=`<circle cx="${m(A.x)}" cy="${u(A.y)}" r="${S}" fill="${E}"/>`,i||(M+=`<text x="${m(A.x)}" y="${u(A.y)}" font-size="9" font-weight="700" text-anchor="middle" dominant-baseline="central" font-family="monospace" fill="${jA(E)}">${A.symbol}</text>`);const D=i?null:v[A.idx];if(D!=null){const X=(+m(A.x)+8.5).toFixed(1),H=(+u(A.y)-8.5).toFixed(1);M+=`<circle cx="${X}" cy="${H}" r="5.5" fill="#fff" stroke="${E}" stroke-width="1.4"/>`,M+=`<text x="${X}" y="${H}" font-size="8" font-weight="700" text-anchor="middle" dominant-baseline="central" font-family="monospace" fill="#0e1b24">${D}</text>`}}else A.symbol!=="C"&&(M+=`<text x="${m(A.x)}" y="${u(A.y)}" font-size="9" text-anchor="middle" dominant-baseline="central" font-family="monospace" fill="currentColor">${A.symbol}</text>`);const R=Math.round(g),C=Math.round(x);return`<svg xmlns="http://www.w3.org/2000/svg" width="${R}" height="${C}" viewBox="0 0 ${R} ${C}">${M}</svg>`}function XA({complex:t,geometry:e,onClose:n,onBuild:i}){const r=Q.useRef(null),s=Q.useRef(null);Q.useEffect(()=>{var I;window.matchMedia("(max-width: 1100px)").matches&&((I=s.current)==null||I.scrollIntoView({block:"start",behavior:gl()?"auto":"smooth"}))},[]);const o=Q.useRef({}),[a,l]=Q.useState(null),[c,d]=Q.useState(""),[h,f]=Q.useState(null),[p,g]=Q.useState([]),[x,m]=Q.useState(""),[u,_]=Q.useState({}),[v,M]=Q.useState(null),[R,C]=Q.useState(null),[A,P]=Q.useState(!1),[E,S]=Q.useState(!1),D=t.ligands.map(I=>I.denticity),X=t.ligands.map((I,z)=>I.is_arene?z:-1).filter(I=>I>=0),H=t.ligands.map((I,z)=>I.pi_sites&&I.pi_sites.length?z:-1).filter(I=>I>=0),U=new Set(H);function Y(I){const z=t.ligands[I],ie=(z==null?void 0:z.coord_atoms)||[],le=((z==null?void 0:z.pi_sites)||[]).filter(pe=>pe.length);if(z!=null&&z.is_arene&&!le.length)return[{sym:"η",cap:!0,atoms:ie}];const ye=R&&R[I],oe=ye&&ye.atoms?new Map(ye.atoms.map(pe=>[pe.idx,pe.symbol])):null,te=le.map(pe=>({sym:"η",cap:!0,atoms:pe})),me=new Set(le.flat());for(const pe of ie)me.has(pe)||te.push({sym:oe&&oe.get(pe)||"?",cap:!1,atoms:[pe]});return te}const V=I=>Y(I).map(z=>z.sym);Q.useEffect(()=>{let I=!1;return St.sites(e,D,X,H).then(z=>{if(I)return;if(z.detail)return d(z.detail);l(z);const ie={};for(const[le,ye]of Object.entries(z.default_assignment))ie[Number(le)]=ye;_(ie)}).catch(z=>!I&&d(String(z))),()=>{I=!0}},[]),Q.useEffect(()=>{let I=!1;return Promise.all(t.ligands.map(z=>St.depict(z.smiles).catch(()=>null))).then(z=>!I&&C(z)),()=>{I=!0}},[]);const J=new Set(((a==null?void 0:a.cis_pairs)||[]).map(([I,z])=>Bu(I,z)));for(const[I,z]of Object.entries(u))for(const ie of z)Number(I);function N(I){if(m(""),h===I){f(null),g([]);return}u[I]!=null&&_(z=>{const ie={...z};return delete ie[I],ie}),f(I),g([])}Q.useEffect(()=>{if(!a||!r.current)return;const I=r.current;let z=I.clientWidth,ie=I.clientHeight;const le=Math.max(...a.sites.map(K=>Math.hypot(K.x,K.y,K.z)),2.5),ye=new _M,oe=new Fn(42,z/ie,.1,100);oe.position.set(le*2.5,le*1.9,le*3.8);const te=new TA({antialias:!0,alpha:!0});te.setSize(z,ie),te.setPixelRatio(window.devicePixelRatio),I.appendChild(te.domElement);const me=new zA;me.setSize(z,ie),Object.assign(me.domElement.style,{position:"absolute",top:"0",left:"0",pointerEvents:"none"}),I.appendChild(me.domElement);const pe=new CA(oe,te.domElement);pe.enableDamping=!gl(),pe.enablePan=!1,pe.minDistance=le*1.4,pe.maxDistance=le*8;const Ue=new ResizeObserver(()=>{z=I.clientWidth,ie=I.clientHeight,!(!z||!ie)&&(oe.aspect=z/ie,oe.updateProjectionMatrix(),te.setSize(z,ie),me.setSize(z,ie))});Ue.observe(I),ye.add(new BM(16777215,.7));const L=new ym(16777215,.85);L.position.set(6,9,7),ye.add(L);const Xe=new ym(12372192,.35);Xe.position.set(-6,-3,-5),ye.add(Xe);const ze=new Tn(new tc(.55,40,40),new Qa({color:Yn.metal,metalness:.55,roughness:.35}));ye.add(ze);const He=document.createElement("div");He.className="vertex-label metal-label",He.textContent=t.metal,ze.add(new ku(He));const Te={},$e={},we=[];a.sites.forEach(K=>{const se=new O(K.x,K.y,K.z),ve=new Cn().setFromPoints([new O(0,0,0),se]);ye.add(new Tu(ve,new El({color:Yn.guide,transparent:!0,opacity:.6})));const Me=new Tn(new tc(.34,32,32),new Qa({color:Yn.empty,metalness:.1,roughness:.55}));Me.position.copy(se),Me.userData={id:K.id},ye.add(Me),Te[K.id]=Me,we.push(Me);const ue=document.createElement("button");ue.type="button",ue.className="vertex-label clickable",ue.dataset.sid=K.id,ue.textContent=String(K.id),ue.setAttribute("aria-label",`Site ${K.id}, empty`),ue.style.pointerEvents="auto",ue.style.cursor="pointer",ue.onclick=Ve=>{Ve.stopPropagation(),o.current.assignSite(K.id)},$e[K.id]=ue;const je=new kt;je.position.copy(se.clone().normalize().multiplyScalar(le+.55)),ye.add(je),je.add(new ku(ue))});const b=new HM,w=new Fe;o.current={scene:ye,camera:oe,renderer:te,labelRenderer:me,controls:pe,ro:Ue,spheres:Te,labels:$e,sitePos:Te,bonds:{},bridges:{},pulses:{},R:le,ui:{active:h,pending:p,assignment:u,denticities:D,cisSet:J,capSet:U}};function G(K){Te[K].material.color.setHex(Yn.danger),setTimeout(()=>ae(),260)}function ne(K){const{ui:se}=o.current;if(se.owner&&se.owner[K]!=null){const je=se.owner[K];_(Ve=>{const Qe={...Ve};return delete Qe[je],Qe}),m("");return}if(se.active==null){m("Select a ligand first (L0, L1 …), then click a site.");return}const ve=se.denticities[se.active],Me=se.pending;if(Me.includes(K))return;if(ve>=2&&Me.length>0&&!(se.capSet&&se.capSet.has(se.active))){const je=!!(t.ligands[se.active]&&t.ligands[se.active].is_arene),Ve=Me.every(F=>se.cisSet.has(Bu(F,K))),Qe=Me.some(F=>se.cisSet.has(Bu(F,K)));if(je?!Ve:!Qe){G(K);const F=`L${se.active}`;m(je?`Site ${K} isn't next to all of ${GA(Me)}. An η-arene needs three mutually neighbouring sites (one face).`:Me.length===1?`Site ${K} isn't next to site ${Me[0]}. ${F} (${tg(ve)}) needs neighbouring (cis) sites.`:`Site ${K} isn't next to any of ${F}'s placed sites (${Me.join(", ")}). A ${tg(ve)} ligand's sites must stay connected.`);return}}m("");const ue=[...Me,K];if(ue.length===ve){if(!gl())for(const F of ue)o.current.pulses[F]=performance.now();const je=se.active,Ve={...se.assignment,[je]:ue};_(Ve),g([]);const Qe=t.ligands.findIndex((F,xe)=>Ve[xe]==null);f(Qe>=0?Qe:null)}else g(ue)}o.current.assignSite=ne;function ae(){const{ui:K}=o.current,se={};for(const[ve,Me]of Object.entries(K.assignment))for(const ue of Me)se[ue]=Number(ve);for(const[ve,Me]of Object.entries(Te)){const ue=Number(ve);se[ue]!=null?Me.material.color.setHex(Yn.bound):K.pending.includes(ue)?Me.material.color.setHex(Yn.pending):Me.material.color.setHex(Yn.empty)}}o.current.paint=ae;const ee=40;o.current.pickAt=(K,se)=>{const ve=te.domElement.getBoundingClientRect();if(K<ve.left||K>ve.right||se<ve.top||se>ve.bottom)return null;w.x=(K-ve.left)/ve.width*2-1,w.y=-((se-ve.top)/ve.height)*2+1,b.setFromCamera(w,oe);const Me=b.intersectObjects(we,!1)[0];if(Me)return Me.object.userData.id;let ue=null,je=ee;for(const[Ve,Qe]of Object.entries(Te)){const F=Qe.position.clone().project(oe),xe=ve.left+(F.x+1)/2*ve.width,q=ve.top+(1-F.y)/2*ve.height,re=Math.hypot(xe-K,q-se);re<je&&(je=re,ue=Number(Ve))}return ue};function Ie(K){const se=te.domElement.getBoundingClientRect();w.x=(K.clientX-se.left)/se.width*2-1,w.y=-((K.clientY-se.top)/se.height)*2+1,b.setFromCamera(w,oe);const ve=b.intersectObjects(we,!1)[0];te.domElement.style.cursor=ve?"pointer":"grab"}function Se(K){const se=o.current.pickAt(K.clientX,K.clientY);se!=null&&ne(se)}te.domElement.addEventListener("pointermove",Ie),te.domElement.addEventListener("click",Se);let Pe;const tt=()=>{Pe=requestAnimationFrame(tt),pe.update();const K=performance.now();for(const[se,ve]of Object.entries(Te)){const Me=o.current.pulses[se];if(Me){const ue=(K-Me)/320;ve.scale.setScalar(ue>=1?1:1+.5*Math.sin(ue*Math.PI)),ue>=1&&delete o.current.pulses[se]}}te.render(ye,oe),me.render(ye,oe)};return tt(),()=>{cancelAnimationFrame(Pe),Ue.disconnect(),te.domElement.removeEventListener("pointermove",Ie),te.domElement.removeEventListener("click",Se),pe.dispose(),te.dispose(),I.removeChild(te.domElement),I.removeChild(me.domElement)}},[a]),Q.useEffect(()=>{const I=o.current;if(!I.spheres)return;const z={};for(const[oe,te]of Object.entries(u))for(const me of te)z[me]=Number(oe);if(I.ui={active:h,pending:p,assignment:u,denticities:D,cisSet:J,capSet:U,owner:z},I.paint(),I.labels){const oe={};for(const[pe,Ue]of Object.entries(u)){const L=V(Number(pe));Ue.forEach((Xe,ze)=>{oe[Xe]=L[ze]??"?"})}const te=h!=null?V(h):[],me=(pe,Ue)=>`<b>${pe}</b><sub style="font-weight:400">${Ue}</sub>`;for(const[pe,Ue]of Object.entries(I.labels)){const L=Number(pe),Xe=z[L]!=null?wh(oe[L]??"?"):"";if(Ue.style.borderColor=Xe,Ue.style.boxShadow=Xe?`inset 0 0 0 1px ${Xe}, 0 1px 3px rgba(14, 27, 36, 0.12)`:"",z[L]!=null)Ue.innerHTML=me(oe[L]??"?",L),Ue.setAttribute("aria-label",`Site ${L}, bound to L${z[L]} (${oe[L]??"?"})`);else if(p.includes(L)){const ze=te[p.indexOf(L)]??"?";Ue.innerHTML=me(ze,L),Ue.setAttribute("aria-label",`Site ${L}, being placed for L${h} (${ze})`)}else Ue.textContent=String(L),Ue.setAttribute("aria-label",`Site ${L}, empty`);Ue.classList.toggle("bound",z[L]!=null)}}const ie=new Set;for(const[oe,te]of Object.entries(u)){const me=t.ligands[oe],pe=((me==null?void 0:me.pi_sites)||[]).filter(Ue=>Ue.length);me!=null&&me.is_arene&&!pe.length?te.forEach(Ue=>ie.add(Ue)):pe.forEach((Ue,L)=>{te[L]!=null&&ie.add(te[L])})}for(const[oe,te]of Object.entries(I.spheres)){const me=Number(oe),pe=z[me]!=null&&!ie.has(me);if(pe&&!I.bonds[me]){const Ue=new Cn().setFromPoints([new O(0,0,0),te.position.clone()]),L=new Tu(Ue,new El({color:Yn.bond}));I.scene.add(L),I.bonds[me]=L}else!pe&&I.bonds[me]&&(I.scene.remove(I.bonds[me]),delete I.bonds[me])}I.caps=I.caps||{};for(const[oe,te]of Object.entries(I.caps))te.forEach(me=>I.scene.remove(me)),delete I.caps[oe];const le=(oe,te,me,pe)=>new Tn(new nc(new Kv(Array.from({length:60},(Ue,L)=>{const Xe=L/60*Math.PI*2;return oe.clone().addScaledVector(te,pe*Math.cos(Xe)).addScaledVector(me,pe*Math.sin(Xe))}),!0),80,.03,8),new Qa({color:Yn.hover,metalness:.1,roughness:.5,transparent:!0,opacity:.6})),ye=oe=>new Tu(new Cn().setFromPoints([new O(0,0,0),oe.clone()]),new El({color:Yn.bond}));for(const[oe,te]of Object.entries(u)){const me=t.ligands[oe],pe=((me==null?void 0:me.pi_sites)||[]).filter(L=>L.length),Ue=[];if(me!=null&&me.is_arene&&!pe.length&&te.length>=3){const L=te.map(we=>I.spheres[we].position.clone()),Xe=new O;L.forEach(we=>Xe.add(we)),Xe.multiplyScalar(1/L.length);const ze=new O().crossVectors(L[1].clone().sub(L[0]),L[2].clone().sub(L[0])).normalize(),He=L[0].clone().sub(Xe).normalize(),Te=new O().crossVectors(ze,He).normalize(),$e=L.reduce((we,b)=>we+b.distanceTo(Xe),0)/L.length;Ue.push(le(Xe,He,Te,$e),ye(Xe))}else pe.length&&pe.forEach((L,Xe)=>{const ze=te[Xe];if(ze==null)return;const He=I.spheres[ze].position.clone(),Te=He.clone().normalize(),$e=Math.abs(Te.y)<.9?new O(0,1,0):new O(1,0,0),we=new O().crossVectors(Te,$e).normalize(),b=new O().crossVectors(Te,we).normalize();Ue.push(le(He,we,b,.42),ye(He))});Ue.length&&(Ue.forEach(L=>I.scene.add(L)),I.caps[oe]=Ue)}for(const[oe,te]of Object.entries(I.bridges))I.scene.remove(te),delete I.bridges[oe];for(const[oe,te]of Object.entries(u))if(te.length===2&&!U.has(Number(oe))){const me=I.spheres[te[0]].position,pe=I.spheres[te[1]].position,Ue=me.clone().add(pe).multiplyScalar(.5).normalize().multiplyScalar(I.R*1.28),L=new Pf(me.clone(),Ue,pe.clone()),Xe=new Tn(new nc(L,20,.06,8),new Qa({color:Yn.bound,metalness:.1,roughness:.5}));I.scene.add(Xe),I.bridges[oe]=Xe}I.depictObjs=I.depictObjs||{};for(const[oe,te]of Object.entries(I.depictObjs))I.scene.remove(te),delete I.depictObjs[oe];if(R)for(const[oe,te]of Object.entries(u)){const me=t.ligands[oe],pe=(me==null?void 0:me.coord_atoms)||[],Ue=((me==null?void 0:me.pi_sites)||[]).filter(we=>we.length),L=!!(me!=null&&me.is_arene)&&!Ue.length,Xe={};if(!L){const we=new Set(Ue.flat());pe.filter(w=>!we.has(w)).forEach((w,G)=>{const ne=te[Ue.length+G];ne!=null&&(Xe[w]=ne)})}const ze=WA(R[oe],pe,Xe,L);if(!ze)continue;const He=new O;for(const we of te)He.add(I.spheres[we].position);He.multiplyScalar(1/te.length).normalize().multiplyScalar(I.R+1.4);const Te=document.createElement("div");Te.className="scene-depict",Te.innerHTML=ze;const $e=new ku(Te);$e.position.copy(He),I.scene.add($e),I.depictObjs[oe]=$e}},[u,h,p,D,R]);function j(I,z){I.preventDefault(),N(z);const ie=I.currentTarget.getBoundingClientRect();M({x0:ie.left+ie.width/2,y0:ie.top+ie.height/2,x1:I.clientX,y1:I.clientY});const le=oe=>M(te=>te&&{...te,x1:oe.clientX,y1:oe.clientY}),ye=oe=>{window.removeEventListener("pointermove",le),window.removeEventListener("pointerup",ye),M(null);const te=document.elementFromPoint(oe.clientX,oe.clientY),me=te&&te.closest?te.closest(".vertex-label[data-sid]"):null,pe=me?Number(me.dataset.sid):o.current.pickAt&&o.current.pickAt(oe.clientX,oe.clientY);pe!=null&&o.current.assignSite(pe)};window.addEventListener("pointermove",le),window.addEventListener("pointerup",ye)}const Z=Object.keys(u).length,fe=Z===t.ligands.length;function _e(){m(""),_({}),g([]),f(t.ligands.length?0:null),S(!0)}async function Re(){const I={};for(const[z,ie]of Object.entries(u))I[z]=ie;P(!0);try{await i(I)}catch{P(!1)}}return y.jsxs("div",{className:"scene-panel card","data-tour":"assign-scene",ref:s,children:[E&&y.jsx("span",{"data-tour":"assign-cleared","aria-hidden":"true",style:{display:"none"}}),y.jsxs("div",{className:"row",style:{justifyContent:"space-between",marginBottom:10},children:[y.jsxs("h2",{style:{margin:0},children:["Isomer editor — ",y.jsx("span",{className:"mono",children:t.name})]}),y.jsx("button",{className:"toggle-btn",onClick:n,children:"Close"})]}),c?y.jsx("span",{className:"pill-err",children:c}):y.jsxs(y.Fragment,{children:[y.jsx("div",{className:"muted",style:{marginBottom:8,fontSize:"var(--text-caption)"},children:"Select a ligand, then click/drag its donor(s) onto numbered sites: a bidentate needs two cis sites, a meridional tridentate three connected sites; a centroid η-cap (Cp/arene, shown η) takes any single site — a metallocene's two caps sit trans. Bound sites show the bound donor; click a bound site to release it; drag the scene to rotate."}),y.jsx("div",{style:{marginBottom:10},"data-tour":"assign-palette",children:t.ligands.map((I,z)=>{var ye;const ie=u[z],le="palette-chip"+(h===z?" active":"")+(ie!=null?" assigned":"");return y.jsxs("button",{type:"button",className:le,"data-smiles":I.smiles,style:{touchAction:"none"},"aria-pressed":h===z,onPointerDown:oe=>j(oe,z),onClick:oe=>{oe.detail===0&&N(z)},children:[h===z?y.jsx("span",{className:"place-cue",children:"▶"}):null,y.jsxs("span",{className:"mono",children:["L",z]})," · ",I.is_arene?`η${((ye=I.coord_atoms)==null?void 0:ye.length)??""}`:HA(I.denticity),y.jsx("span",{className:"chip-smiles mono",children:VA(I.smiles)}),I.is_arene?ie!=null?y.jsxs("span",{className:"mono",children:[" → ",ie.join(",")]}):null:y.jsx("span",{style:{display:"inline-flex",gap:4,marginLeft:6,verticalAlign:"middle"},children:V(z).map((oe,te)=>y.jsxs("span",{title:`donor ${oe}${ie!=null&&ie[te]!=null?` → site ${ie[te]}`:""}`,style:{display:"inline-flex",alignItems:"center",gap:2,padding:"0 5px",borderRadius:9,border:`1.3px solid ${wh(oe)}`,color:"inherit",fontFamily:"var(--mono)",fontSize:"var(--text-caption)",fontWeight:500,lineHeight:1.35},children:[oe,ie!=null&&ie[te]!=null?y.jsxs("span",{style:{fontWeight:400},children:["→",ie[te]]}):null]},te))})]},z)})}),y.jsx("div",{className:"scene-wrap",ref:r}),y.jsxs("div",{className:"row",style:{marginTop:12,justifyContent:"space-between"},children:[y.jsxs("span",{className:"muted",children:[Z,"/",t.ligands.length," ligands placed"]}),y.jsxs("div",{className:"row",style:{gap:8},children:[y.jsx("button",{className:"ghost","data-tour":"assign-disconnect",disabled:Z===0||A,onClick:_e,children:"Disconnect all"}),y.jsx("button",{className:"primary","data-tour":fe?"assign-build":void 0,disabled:!fe||A,onClick:Re,children:y.jsx(Qo,{busy:A,label:"Save this isomer",busyLabel:"Saving…"})})]})]}),y.jsx("div",{className:"place-error",role:"status",children:x})]}),v&&y.jsxs("svg",{style:{position:"fixed",inset:0,width:"100%",height:"100%",pointerEvents:"none",zIndex:60},children:[y.jsx("line",{x1:v.x0,y1:v.y0,x2:v.x1,y2:v.y1,style:{stroke:"var(--accent-500)"},strokeWidth:"2",strokeDasharray:"5 4"}),y.jsx("circle",{cx:v.x1,cy:v.y1,r:"5",style:{fill:"var(--accent-bright)"}})]})]})}const ng=[{label:"NH₃",name:"Ammonia",smiles:"N"},{label:"H₂O",name:"Water",smiles:"O"},{label:"CO",name:"Carbon monoxide",smiles:"[C-]#[O+]"},{label:"Cl⁻",name:"Chloride",smiles:"[Cl-]"},{label:"Br⁻",name:"Bromide",smiles:"[Br-]"},{label:"I⁻",name:"Iodide",smiles:"[I-]"},{label:"CN⁻",name:"Cyanide",smiles:"[C-]#N"},{label:"OH⁻",name:"Hydroxide",smiles:"[OH-]"},{label:"py",name:"Pyridine",smiles:"c1ccncc1"},{label:"bipy",name:"2,2′-Bipyridine",smiles:"c1ccc(-c2ccccn2)nc1"},{label:"phen",name:"1,10-Phenanthroline",smiles:"C1(C(N=CC=C2)=C2C=C3)=C3C=CC=N1"},{label:"terpy",name:"2,2′:6′,2″-Terpyridine",smiles:"c1ccnc(-c2cccc(-c3ccccn3)n2)c1"},{label:"en",name:"Ethylenediamine",smiles:"NCCN"},{label:"PPh₃",name:"Triphenylphosphine",smiles:"P(c1ccccc1)(c1ccccc1)c1ccccc1"},{label:"acac",name:"Acetylacetonate",smiles:"CC(CC(C)[O-])[O-]"},{label:"OAc⁻",name:"Acetate",smiles:"CC(=O)[O-]"},{label:"ox²⁻",name:"Oxalate",smiles:"C(=O)(C(=O)[O-])[O-]"},{label:"Cp⁻",name:"Cyclopentadienyl",smiles:"[cH-]1cccc1"},{label:"MeCN",name:"Acetonitrile",smiles:"CC#N"},{label:"DMSO",name:"Dimethyl sulfoxide",smiles:"CS(=O)C"},{label:"SCN⁻",name:"Thiocyanate",smiles:"[S-]C#N"},{label:"NO₂⁻",name:"Nitrite",smiles:"O=N[O-]"}];function $A({lig:t,svg:e,onInsert:n}){return y.jsxs("button",{type:"button",className:"lig-box",title:`${t.name} — ${t.smiles}  (click to insert)`,onClick:()=>n(t.smiles),children:[y.jsx("span",{className:"lig-thumb","aria-hidden":"true",children:e?y.jsx("span",{className:"lig-thumb-svg",dangerouslySetInnerHTML:{__html:e}}):y.jsx("span",{className:"lig-thumb-wait"})}),y.jsx("span",{className:"lig-box-name",children:t.label})]})}function YA({onInsert:t,onClose:e}){const[n,i]=Q.useState({});return Q.useEffect(()=>{let r=!1;return Promise.all(ng.map(s=>St.depictSvg(s.smiles).then(o=>[s.smiles,(o==null?void 0:o.svg)||null]).catch(()=>[s.smiles,null]))).then(s=>!r&&i(Object.fromEntries(s))),()=>{r=!0}},[]),y.jsxs("div",{className:"ligand-library card","data-tour":"ligand-library-panel",children:[y.jsxs("div",{className:"lig-lib-head",children:[y.jsx("h2",{children:"Ligand library"}),y.jsx("button",{className:"toggle-btn",onClick:e,title:"Close the ligand library",children:"Close"})]}),y.jsx("p",{className:"muted lig-lib-hint",children:"Click a ligand to drop its SMILES at the cursor."}),y.jsx("div",{className:"lig-reel",children:y.jsx("div",{className:"lig-reel-track",children:ng.map(r=>y.jsx($A,{lig:r,svg:n[r.smiles],onInsert:t},r.smiles))})})]})}const zu=20;function qA(t){if(t.length<=zu+4)return-1;const e=t.lastIndexOf("_"),n=e>0?t.lastIndexOf("_",e-1):-1;return n>0&&t.length-n<=zu?n:e>0&&t.length-e<=zu?e:t.length-16}function s0({text:t}){const e=String(t??""),n=qA(e);return n<0?y.jsx("span",{className:"mid-name",children:y.jsx("span",{className:"mid-name-head",children:e})}):y.jsxs("span",{className:"mid-name",children:[y.jsx("span",{className:"mid-name-head",children:e.slice(0,n)}),y.jsx("span",{className:"mid-name-tail",children:e.slice(n)})]})}const ig=(t,e)=>{const n=e||t<=1?1:t===2||t<=4?2:3;return{cols:n,rows:Math.ceil(t/n)}};function KA(){const[t,e]=Q.useState(()=>typeof window<"u"&&window.matchMedia("(max-width: 640px)").matches);return Q.useEffect(()=>{const n=window.matchMedia("(max-width: 640px)"),i=()=>e(n.matches);return n.addEventListener("change",i),()=>n.removeEventListener("change",i)},[]),t}const rg=new Set(["H","B","C","N","O","F","Si","P","S","Cl","Se","Br","I"]),ZA=2.9,JA=(t,e)=>Math.hypot(t.x-e.x,t.y-e.y,t.z-e.z);function sg(t,e,n){t.addCylinder({start:{x:e.x,y:e.y,z:e.z},end:{x:n.x,y:n.y,z:n.z},radius:.12,fromCap:1,toCap:1,color:"0x9c95f0"})}function QA(t,e){for(const n of t)if(n.bonds){if(n===e){n.bonds=[],n.bondOrder=[];continue}for(let i=n.bonds.length-1;i>=0;i--)n.bonds[i]===e.index&&(n.bonds.splice(i,1),n.bondOrder&&n.bondOrder.splice(i,1))}}function eC(t,e){const n=new Set(t.map(s=>s.index)),i=new Set,r=[];for(const s of t){if(i.has(s.index))continue;const o=[],a=[s];for(i.add(s.index);a.length;){const l=a.pop();o.push(l);for(const c of l.bonds||[])n.has(c)&&!i.has(c)&&(i.add(c),a.push(e.get(c)))}r.push(o)}return r}function tC(t,e,n){const i=t.selectedAtoms({}),r=new Map(i.map(c=>[c.index,c])),s=e!=null?r.get(e):i.find(c=>!rg.has(c.elem));if(!s)return;QA(i,s);const o=i.filter(c=>c!==s&&c.elem!=="H"&&rg.has(c.elem)),a=c=>JA(c,s)<=ZA,l=n&&n.length?n.map(c=>r.get(c)).filter(Boolean):o.filter(a);for(const c of eC(l,r))if(c.length>=3){const d=new Set(c.map(p=>p.index));for(let p=!0;p;){p=!1;for(const g of o)d.has(g.index)||!a(g)||(g.bonds||[]).some(x=>d.has(x))&&(d.add(g.index),p=!0)}const h=[...d].map(p=>r.get(p)).filter(Boolean),f=h.reduce((p,g)=>({x:p.x+g.x,y:p.y+g.y,z:p.z+g.z}),{x:0,y:0,z:0});sg(t,s,{x:f.x/h.length,y:f.y/h.length,z:f.z/h.length})}else for(const d of c)sg(t,s,d)}function nC({items:t}){const e=Q.useRef(null),n=KA(),i=t.map(o=>o.token).join(",");if(Q.useEffect(()=>{const o=e.current;if(!o||!window.$3Dmol||!t.length)return;let a=!1;return Promise.all(t.map(l=>St.fileText(l.token))).then(l=>{if(a)return;o.innerHTML="";const{rows:c,cols:d}=ig(t.length,n),h=window.$3Dmol.createViewerGrid(o,{rows:c,cols:d,control_all:!0},{backgroundColor:"0x0E1B24"});l.forEach((f,p)=>{const g=h[Math.floor(p/d)][p%d];g.addModel(f,"xyz"),tC(g,t[p].metalIndex,t[p].donorIndices),g.setStyle({},{stick:{radius:.14},sphere:{scale:.25}}),g.zoomTo(),g.render()})}),()=>{a=!0}},[i,n]),!t.length)return null;const{rows:r,cols:s}=ig(t.length,n);return y.jsxs("div",{className:"viewer-grid",style:{height:(n?130:180)+r*(n?220:240)},children:[y.jsx("div",{className:"viewer-grid-canvas",ref:e}),t.map((o,a)=>y.jsxs("span",{className:"viewer-grid-label mono",style:{left:`calc(${a%s*(100/s)}% + 8px)`,top:`calc(${Math.floor(a/s)*(100/r)}% + 8px)`,maxWidth:`calc(${100/s}% - 16px)`},children:[o.isomer_label?y.jsxs("span",{className:"vg-iso",children:[o.isomer_label," · "]}):null,y.jsx(s0,{text:o.name})]},o.token))]})}const Tl=9;function iC({files:t,viewTokens:e,onViewTokens:n,onRemove:i,onRemoveAll:r}){const[s,o]=Q.useState({}),[a,l]=Q.useState(null),[c,d]=Q.useState(null),[h,f]=Q.useState(!1),[p,g]=Q.useState(!1),[x,m]=Q.useState({}),[u,_]=Q.useState([]);if(Q.useEffect(()=>{St.reverseBackends().then(E=>_(E.representations||[])).catch(()=>{})},[]),!(t!=null&&t.length))return null;const v=e.length>=Tl,M=E=>{if(e.includes(E))return n(e.filter(D=>D!==E));if(v)return;const S=new Set([...e,E]);n(t.filter(D=>S.has(D.token)).map(D=>D.token))},R=async(E,S,D)=>{l(null),o(X=>({...X,[E]:{loading:!0}}));try{const X=await St.fileText(E),H=await St.represent(X,D.key,(S==null?void 0:S.total_charge)??0);o(U=>({...U,[E]:{result:H}}))}catch(X){o(H=>({...H,[E]:{error:X.message}}))}},C=async E=>{f(!1),g(!0);try{const S=await Promise.all(t.map(async J=>({name:J.name,xyz:await St.fileText(J.token),overall_charge:J.total_charge??0}))),{csv:D}=await St.reverseExport(S,E),X=URL.createObjectURL(new Blob([D],{type:"text/csv"})),H=document.createElement("a");H.href=X;const U=new Date,Y=J=>String(J).padStart(2,"0"),V=`${U.getFullYear()}-${Y(U.getMonth()+1)}-${Y(U.getDate())}_${Y(U.getHours())}${Y(U.getMinutes())}${Y(U.getSeconds())}`;H.download=`mecobi_smiles_${V}.csv`,H.click(),URL.revokeObjectURL(X)}catch(S){window.alert(`Export failed: ${S.message}`)}finally{g(!1)}},A=t[0].token.split("/")[0],P=()=>{const E=t.length;window.confirm(`Clear ${E} result${E===1?"":"s"} from this list? Download them first if you need them.`)&&(r==null||r())};return y.jsxs("div",{className:"card","data-tour":"results-card",children:[y.jsxs("div",{className:"results-head",children:[y.jsx("h2",{style:{margin:0},children:"Results"}),y.jsxs("span",{className:"results-count muted",children:["rendering ",e.length," of ",t.length,v?` · max ${Tl}`:""]}),y.jsx("span",{className:"grow"}),y.jsxs("span",{className:"result-actions",children:[y.jsx("span",{className:"actions-label muted","aria-hidden":"true",children:"All structures:"}),y.jsx("a",{className:"ghost",href:St.downloadAllUrl(A),download:!0,title:"Download all structures as a zip",children:"Download all (zip)"}),u.length?y.jsxs("span",{className:"smiles-btn",children:[y.jsx("button",{className:"ghost",title:"Export SMILES / notation for all results as a CSV",disabled:p,onClick:()=>u.length===1?C([u[0].key]):f(E=>!E),children:y.jsx(Qo,{busy:p,label:"Export CSV ▾",busyLabel:"Exporting…"})}),h?y.jsxs("div",{className:"smiles-menu",onMouseLeave:()=>f(!1),children:[u.map(E=>y.jsxs("button",{className:"smiles-item",title:E.cite||void 0,onClick:()=>C([E.key]),children:[y.jsx("span",{children:E.label}),E.ref?y.jsx("em",{className:"ref",children:E.ref}):null]},E.key)),u.length>1?y.jsx("button",{className:"smiles-item",onClick:()=>C(u.map(E=>E.key)),children:"All columns"}):null]}):null]}):null,r?y.jsx("button",{className:"ghost",title:"Clear all results",onClick:P,children:"Remove all"}):null]})]}),t.map(E=>{var D,X,H;const S=s[E.token];return y.jsxs("div",{className:"result-item-wrap",children:[y.jsxs("div",{className:"result-item",children:[y.jsx("input",{type:"checkbox",checked:e.includes(E.token),disabled:!e.includes(E.token)&&v,onChange:()=>M(E.token),title:`Show in the 3D grid (up to ${Tl})`}),y.jsxs("span",{className:"name",title:E.name,children:[y.jsx(s0,{text:E.name}),E.is_lowest_energy?y.jsx("span",{className:"chip chip-star",title:"lowest GFN2 energy",children:"★"}):null,E.relative_energy_kcal!=null?y.jsxs("span",{className:"res-energy",title:"relative GFN2 energy",children:["+",E.relative_energy_kcal.toFixed(1)," kcal/mol"]}):null]}),(D=E.warnings)!=null&&D.length?y.jsx("button",{type:"button",className:`res-warn${x[E.token]?" open":""}`,"aria-expanded":!!x[E.token],title:`${E.warnings.length} build warning${E.warnings.length>1?"s":""}: click to ${x[E.token]?"hide":"show"}`,onClick:()=>m(U=>({...U,[E.token]:!U[E.token]})),children:"⚠"}):y.jsx("span",{}),y.jsxs("span",{className:"result-actions",children:[y.jsx("button",{className:"ghost",onClick:()=>n([E.token]),children:"View"}),u.length?y.jsxs("span",{className:"smiles-btn",children:[y.jsx("button",{className:"ghost",title:"Get SMILES / notation for this structure",disabled:S==null?void 0:S.loading,onClick:()=>u.length===1?R(E.token,E,u[0]):l(a===E.token?null:E.token),children:y.jsx(Qo,{busy:!!(S!=null&&S.loading),label:u.length===1?"Get SMILES":"Get SMILES ▾",busyLabel:"Getting…"})}),a===E.token?y.jsx("div",{className:"smiles-menu",onMouseLeave:()=>l(null),children:u.map(U=>y.jsxs("button",{className:"smiles-item",title:U.cite||void 0,onClick:()=>R(E.token,E,U),children:[y.jsx("span",{children:U.label}),U.ref?y.jsx("em",{className:"ref",children:U.ref}):null]},U.key))}):null]}):null,E.formats&&E.formats.length>1?y.jsxs("span",{className:"smiles-btn",children:[y.jsx("button",{className:"ghost",title:"Download this structure (choose a format)",onClick:()=>d(c===E.token?null:E.token),children:"Download ▾"}),c===E.token?y.jsx("div",{className:"smiles-menu",onMouseLeave:()=>d(null),children:E.formats.map(U=>y.jsx("a",{className:"smiles-item",href:St.fileUrlAs(E.token,U),download:!0,onClick:()=>d(null),children:y.jsx("span",{children:U.toUpperCase()})},U))}):null]}):y.jsx("a",{className:"ghost",href:St.fileUrl(E.token),download:!0,children:"Download"}),i?y.jsx("button",{className:"ghost",title:"Remove from results",onClick:()=>i(E.token),children:"Remove"}):null]})]}),x[E.token]&&((X=E.warnings)!=null&&X.length)?y.jsx("ul",{className:"res-warn-list",children:[...new Set(E.warnings)].map(U=>y.jsx("li",{children:U},U))}):null,S!=null&&S.error?y.jsx("div",{style:{marginTop:4},children:y.jsx("span",{className:"pill-err",children:S.error})}):null,S!=null&&S.result?y.jsxs("div",{className:"reverse-out",children:[y.jsxs("span",{className:"muted",children:[S.result.label,(H=u.find(U=>U.key===S.result.key))!=null&&H.ref?y.jsxs("em",{className:"ref",children:[" ",u.find(U=>U.key===S.result.key).ref]}):null,":"]}),y.jsx("span",{className:"mono reverse-lig",children:S.result.value})]}):null]},E.token)}),y.jsx("div",{style:{marginTop:14},children:y.jsx(nC,{items:e.map(E=>{const S=t.find(D=>D.token===E);return{token:E,name:(S==null?void 0:S.name)||"",isomer_label:(S==null?void 0:S.isomer_label)??null,metalIndex:(S==null?void 0:S.metal_index)??null,donorIndices:(S==null?void 0:S.donor_indices)||null}})})})]})}function rC(){const[t,e]=Q.useState(null);return Q.useEffect(()=>{let n=!1;return fetch("/api/workload").then(i=>i.ok?i.json():null).then(i=>{!n&&i&&e(i)}).catch(()=>{}),()=>{n=!0}},[]),(t==null?void 0:t.max_complexes_per_job)==null||(t==null?void 0:t.max_pending_structures)==null?null:y.jsxs("div",{className:"muted web-limit-note",children:["Web limit: ",t.max_complexes_per_job.toLocaleString()," complexes per job;"," ",t.max_pending_structures.toLocaleString()," unfinished structures across the server"," ","(with all isomers, each isomer counts)."]})}function sC(){const[t,e]=Q.useState(null);if(Q.useEffect(()=>{let r=!1,s;const o=new AbortController;async function a(){try{const l=await fetch("/api/workload",{signal:o.signal});if(!l.ok)throw new Error("Workload unavailable");const c=await l.json();r||e(c)}catch{r||e(null)}finally{r||(s=setTimeout(a,1e4))}}return a(),()=>{r=!0,clearTimeout(s),o.abort()}},[]),!t||!t.busy)return null;const n=t.longest_running_s>=t.long_job_seconds,i=Math.max(1,Math.ceil(t.estimated_wait_s/60));return y.jsx("div",{style:{marginBottom:16},children:y.jsxs("div",{className:"pill-warn",role:"status",style:{display:"block",whiteSpace:"normal"},children:[y.jsx("strong",{children:n?"A long job is running.":"The server is busy."})," ","Use Build all to join the queue. Individual builds are available when the server is free.",t.queued_jobs>0&&y.jsxs(y.Fragment,{children:[" ",t.queued_jobs," job",t.queued_jobs===1?"":"s"," queued."]}),t.estimated_wait_s>0&&y.jsxs(y.Fragment,{children:[" Existing work is estimated at about ",i," minute",i===1?"":"s","."]})," ","Estimates are approximate; large molecules and multiple isomers can take longer."]})})}const oC=[{title:"Welcome to MeCoBi",body:"MeCoBi turns the SMILES of a metal complex's ligands into optimised 3D structures. This quick tour walks through the interface with real examples. Reopen it any time from “Tour” at the top-right."},{target:"input-card",title:"1 · Describe your complexes",body:"Type or paste one complex per line: the metal, its oxidation state, then each ligand as SMILES, separated by commas."},{target:"input-card",title:"2 · Load an example",body:"You can load sample structures to see how MeCoBi works. For the tour I've loaded two into the box: cisplatin and ferroquine.",action:"loadSample"},{target:"ligand-library-btn",title:"Common ligands",body:"Browse a library of frequent ligands (CO, bipy, Cp, chloride…) and click one to drop its SMILES straight into the input box."},{target:"parse-btn",title:"3 · Parse",body:"Now click Parse to read them into a table. The tour continues once the table appears.",waitFor:"complex-table",waitLabel:"Click Parse to continue",interactive:!0},{target:"complex-table",title:"4 · Review the table",body:"Each row is one complex: here cisplatin and ferroquine, with its metal, coordination number, geometry, and ligands."},{target:"ferroquine-donors",title:"5 · Donor atoms",body:"MeCoBi works out which atoms coordinate. Untick ferroquine's Donors box to see what it found.",waitFor:"donor-panel",waitLabel:"Untick ferroquine's Donors box",interactive:!0},{target:"donor-panel",title:"It recognised the Cp rings",body:"MeCoBi has marked all five carbons of each cyclopentadienyl (Cp) ring as coordinating: it read both rings as η5 caps. Click ✓ to keep the selection or ✕ to discard it.",waitGone:"donor-panel",waitLabel:"Save (✓) or Cancel (✕) to continue",interactive:!0},{target:"build-controls",title:"6 · Relaxation settings",body:"Toggle xtb (GFN2) geometry relaxation, choose the spin state, and cap the time per structure. “Advanced options” exposes the pre-xtb geometry guards."},{target:"assign-btn",title:"7 · Set up one exact isomer",body:"Cisplatin's two chlorides are cis. Let's set up the trans isomer, transplatin, by hand. Click Isomer editor on cisplatin's row to open it.",waitFor:"assign-scene",waitLabel:"Click Isomer editor to continue",interactive:!0},{target:"assign-disconnect",title:"Start from a clean slate",body:"The scene opens with cisplatin's ligands already placed (cis). Click Disconnect all to clear the sites and place them yourself. The first ligand then becomes active (highlighted).",waitFor:"assign-cleared",waitLabel:"Click Disconnect all",interactive:!0},{target:"assign-scene",title:"Place the ligands",body:"The highlighted chip is the active ligand. Click a numbered site to seat it, and the next ligand highlights automatically. For transplatin, put the two chlorides on OPPOSITE (trans) sites and the two ammines on the other pair. Drag anywhere in the scene to rotate it.",waitFor:"assign-build",waitLabel:"Place all four ligands on their sites",interactive:!0},{target:"assign-scene",title:"Save this isomer",body:"All four are placed. Drag to rotate and check your isomer, then click Save this isomer (below the scene) to remember transplatin. It does not build yet.",waitFor:"custom-isomer-flag",waitLabel:"Click Save this isomer",interactive:!0},{target:"custom-isomer-flag",title:"Your isomer is remembered",body:"The row now shows a custom-isomer flag. MeCoBi stored your placement, so Build all will build transplatin for cisplatin and the default sandwich for ferroquine. Clear it with the × any time."},{target:"build-all-btn",title:"8 · Build everything",body:"Last step: Build all queues every row as one job and builds them. Click it now to build your transplatin and the ferroquine sandwich. With xtb relaxation on, this can take a little while.",waitFor:"results-card",waitLabel:"Click Build all (this can take a moment)",interactive:!0},{target:"results-card",title:"9 · Your structures",body:"Here they are. Drag a structure to rotate it, tick others to compare side by side, download as .xyz / .mol / .pdb, or convert them back to SMILES / T-REX.",interactive:!0},{title:"That's the tour!",body:"You're set: describe complexes, Parse, then Build or Build all to generate 3D structures. Reopen this any time from “Tour”. Happy building!"}],Hu="https://doi.org/10.26434/chemrxiv.15011867/v1",Vu="https://github.com/TheFreiLab/MeCoBi",aC=`Index,Name,Metal,Charge,L1,L2,L3,L4,L5,L6
1,Cisplatin,Pt,2,N,N,[Cl-],[Cl-],,
2,Titanocene dichloride,Ti,4,[cH-]1cccc1,[cH-]1cccc1,[Cl-],[Cl-],,
3,TLD1433,Ru,2,CC1=CC(=NC=C1)C2=NC=CC(=C2)C,CC1=CC(=NC=C1)C2=NC=CC(=C2)C,C1=CC2=C3C(=C4C=CC=NC4=C2N=C1)N=C(N3)C5=CC=C(S5)C6=CC=C(S6)C7=CC=CS7,,,
4,Ferroquine,Fe,2,CN(C)Cc1cc[cH-]c1CNc2ccnc3cc(Cl)ccc23,[cH-]1cccc1,,,,
5,BOLD-100,Ru,3,[Cl-],[Cl-],[Cl-],[Cl-],c1ccc2c(c1)cn[nH]2,c1ccc2c(c1)cn[nH]2`,lC=`Pt, 2, N, N, [Cl-], [Cl-]
Fe, 2, CN(C)Cc1cc[cH-]c1CNc2ccnc3cc(Cl)ccc23, [cH-]1cccc1`,o0=[{label:"Before optimisation — fix the starting geometry",items:[["orient_bulky","Orient bulky ligands","Swing bulky ligands (e.g. phosphines) away from the metal before xtb so they don't clash."],["reposition_donors","Reposition loose donors","Pull a stranded monodentate donor in to its CSD-average metal–ligand distance."],["clear_metal_region","Clear the metal region","Rotate a monodentate whose backbone folded across the metal out of the way."],["declash_torsion","De-clash by rotation","Spin crowded bulky monodentates about the metal–donor axis so they mesh together."],["mchammer","Force-field pre-placement","Run stk's MCHammer force-field placement pass (off = hand xtb the raw ideal placement)."],["reembed_crowded","Untangle crowded ligands","When bulky ligands (monodentates or chelates) come out threaded through each other (e.g. Pt(PPh₃)₄, Pt(BINAP)₂), re-embed the whole complex at once with the donors held in place."],["reposition_polydentates","Reposition loose chelates","Pull stranded chelates/pincers in to their CSD metal–ligand distance — helps a crowded sphere xtb can't pull in, but usually washes out after relaxation."]]},{label:"During optimisation — xtb constraints",items:[["linear_restraint","Keep linear donors straight","Hold CN⁻/CO/azide/nitrosyl donors linear (M–C≡N ≈ 180°)."],["haptic_guard","Prevent σ→η slip","Pin σ aryl-carbon donors so xtb can't slip them to an η-arene interaction."],["planar_guard","Keep flat donors coplanar","Keep monodentate sp² N/O donors coplanar with the metal."],["antifusion_guard","Undo atom fusion","Re-relax with floors if xtb fuses two donors together."],["oxo_antifusion_floors","Protect terminal oxo/nitrido","Last resort: pin terminal oxo/nitrido at their starting distances from nearby ligand atoms from the FIRST relax. Only if the default build fuses an oxo onto a donor — it freezes a poorly seated oxo and can lengthen M=O."],["metal_surrogate","Metal stand-in relax","Relax a GFN2-divergent metal (e.g. Y) as an xtb-friendly stand-in (Sc), then restore it."]]}],cC=new Set(["metal_surrogate","reposition_polydentates","oxo_antifusion_floors"]),og=Object.fromEntries(o0.flatMap(t=>t.items).map(([t])=>[t,!cC.has(t)]));function uC(){const[t,e]=Q.useState(()=>localStorage.getItem("mecobi-theme")||"light");return Q.useEffect(()=>{document.documentElement.setAttribute("data-theme",t),localStorage.setItem("mecobi-theme",t)},[t]),[t,()=>e(n=>n==="dark"?"light":"dark")]}function ag(t){var n;const e=(t.ligands||((n=t.sel)==null?void 0:n.ligands)||[]).map(i=>i.smiles);return`${t.metal}|${t.oxidation_state}|${e.slice().sort().join("~")}`}function dC(t){const[e,n,i]=t.split("-").map(Number),r=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][n-1];return r?`${i} ${r} ${e}`:t}function lg(t){const e=Math.floor(t/60),n=t%60;return e?`${e}m ${String(n).padStart(2,"0")}s`:`${n}s`}const cg=4e6,hC=new Set(["","text/csv","text/plain","application/csv","application/vnd.ms-excel"]);function fC(t){return/\.csv$/i.test(t.name)?hC.has(t.type)?t.size>cg?`File too large (max ${cg/1e6} MB).`:"":`That doesn't look like a CSV file (type: ${t.type}).`:"Please upload a .csv file."}function pC(t){return{geometry:t.proposed_geometry,allIsomers:!1,stereo:!0,donorsCorrect:!0,ligands:t.ligands.map(e=>({smiles:e.smiles,coord_atoms:e.coord_atoms,is_arene:e.is_arene}))}}const Uo=t=>{var e;return t.is_arene?3:((e=t.coord_atoms)==null?void 0:e.length)||0};function mC(t){const e=t.filter(i=>i.is_arene);if(e.length!==2||!e.every(i=>Uo(i)===3))return null;const n=t.filter(i=>!i.is_arene);return n.length===0?"metallocene":n.every(i=>Uo(i)===1)?"metallocene_bent":null}function Gu(t,e,n,i){return{name:t.name,metal:t.metal,oxidation_state:t.oxidation_state,ligands:t.sel.ligands,geometry:t.sel.geometry,all_isomers:t.sel.allIsomers,stereo:t.sel.stereo,site_assignment:t.sel.siteAssignment||null,relax:e,spin:n,xtb_timeout_s:i}}function gC(){const[t,e]=uC(),[n,i]=Q.useState(""),[r,s]=Q.useState([]),[o,a]=Q.useState(!0),[l,c]=Q.useState("low"),[d,h]=Q.useState(300),[f,p]=Q.useState({...og}),[g,x]=Q.useState(""),[m,u]=Q.useState(""),[_,v]=Q.useState(null),[M,R]=Q.useState(!1),[C,A]=Q.useState(null),[P,E]=Q.useState(!1),S=Q.useRef(null),[D,X]=Q.useState(!1),[H,U]=Q.useState(null),[,Y]=Q.useState(0),[V,J]=Q.useState(!1),[N,j]=Q.useState(null),[Z,fe]=Q.useState(null),_e=Q.useRef(null),Re=Q.useRef(null),[I,z]=Q.useState(""),[ie,le]=Q.useState(""),[ye,oe]=Q.useState("");function te(ce,ge=!1){(ge?oe:le)(Be=>Be===ce?ce+" ":ce)}const[me,pe]=Q.useState([]),[Ue,L]=Q.useState([]),[Xe,ze]=Q.useState(null),[He,Te]=Q.useState(null),[$e,we]=Q.useState(null),[b,w]=Q.useState(!1),G=Q.useRef(null),[ne,ae]=Q.useState(!1),[ee,Ie]=Q.useState(!1);function Se(ce){const ge=`${ce}, `,Be=G.current;if(!Be){i(At=>At+ge);return}const Le=Be.selectionStart??n.length,rt=Be.selectionEnd??n.length,ke=n.slice(0,Le)+ge+n.slice(rt);i(ke),requestAnimationFrame(()=>{Be.focus();const At=Le+ge.length;Be.setSelectionRange(At,At)})}Q.useEffect(()=>{if(localStorage.getItem("mecobi-tour-opened"))return;Ie(!0);const ce=setTimeout(()=>Ie(!1),7e3);return()=>clearTimeout(ce)},[]);const Pe=()=>{Ie(!1),localStorage.setItem("mecobi-tour-opened","1"),ae(!0)},tt=()=>i(ce=>ce.trim()?ce:lC),K=t==="dark"?Oy:Uy,se=Q.useRef(null),[ve,Me]=Q.useState(!1);Q.useEffect(()=>{const ce=se.current;if(!ce)return;const ge=new IntersectionObserver(([Be])=>Me(!Be.isIntersecting),{threshold:0});return ge.observe(ce),()=>ge.disconnect()},[]),Q.useEffect(()=>{St.version().then(we).catch(()=>{})},[]),Q.useEffect(()=>{St.geometries().then(Te).catch(()=>{})},[]);async function ue(ce=n){if(!ce.trim()){x("Paste a CSV first (or load the sample).");return}R(!0),x(""),u(""),v(null);try{const ge=await St.parse(ce),Be=new Set(r.map(ag)),Le=[];for(const ke of ge){const At=ag(ke);Be.has(At)||(Be.add(At),Le.push(ke))}s(ke=>[...ke,...Le.map(At=>({...At,sel:pC(At)}))]),Le.length&&!V&&!P&&(pe([]),L([]),z(""),j(null),U(null),fe(null),_e.current=null,window.location.hash.startsWith("#job=")&&history.replaceState(null,"",window.location.pathname+window.location.search));const rt=ge.length-Le.length;x(Le.length?`${Le.length} complex${Le.length===1?"":"es"} added${rt?` (${rt} already in the list)`:""}.`:"Already in the list — nothing new to add.")}catch(ge){x(""),u(ge.message)}finally{R(!1)}}function je(ce,ge){const Be=ge.geometry!==void 0&&ge.siteAssignment===void 0?{...ge,siteAssignment:null}:ge;s(Le=>Le.map((rt,ke)=>ke===ce?{...rt,sel:{...rt.sel,...Be}}:rt))}function Ve(ce){const ge=He?Object.keys(He).map(Number).sort((Be,Le)=>Be-Le):[];return`No supported geometry for coordination number ${ce}`+(ge.length?` (supported: ${ge[0]} to ${ge[ge.length-1]}).`:".")}function Qe(ce,ge){const Be=ge.reduce((At,Yt)=>At+Uo(Yt),0),Le=mC(ge),rt=He&&He[Be]||[],ke=Le?[Le,...rt]:rt;return{...ce,coordination_number:Be,geometry_options:ke,supported:ke.length>0,error:ke.length?null:Ve(Be),ligands:ce.ligands.map((At,Yt)=>({...At,denticity:Uo(ge[Yt]),coord_atoms:ge[Yt].coord_atoms,is_arene:ge[Yt].is_arene})),sel:{...ce.sel,ligands:ge,geometry:ke.includes(ce.sel.geometry)?ce.sel.geometry:ke[0],siteAssignment:null}}}async function F(ce,ge){const Be=r[ce];let Le=null;try{Le=await St.perceive({metal:Be.metal,oxidation_state:Be.oxidation_state,ligands:ge.map(rt=>({smiles:rt.smiles,coord_atoms:rt.coord_atoms,is_arene:rt.is_arene}))})}catch{}s(rt=>rt.map((ke,At)=>{if(At!==ce)return ke;if(!Le)return Qe(ke,ge);const Yt=Le.geometry_options||[];return{...ke,coordination_number:Le.coordination_number,geometry_options:Yt,needs_cap_selection:!!Le.needs_cap_selection,supported:Yt.length>0,error:Yt.length?null:Le.error||Ve(Le.coordination_number),ligands:ke.ligands.map((Yr,pi)=>{var T,k,W,$;return{...Yr,denticity:((k=(T=Le.ligands)==null?void 0:T[pi])==null?void 0:k.denticity)??Uo(ge[pi]),coord_atoms:ge[pi].coord_atoms,is_arene:ge[pi].is_arene,pi_sites:(($=(W=Le.ligands)==null?void 0:W[pi])==null?void 0:$.pi_sites)??Yr.pi_sites??[]}}),sel:{...ke.sel,ligands:ge,geometry:Yt.includes(ke.sel.geometry)?ke.sel.geometry:Le.proposed_geometry||Yt[0]}}}))}function xe(ce,ge){s(Be=>Be.map(Le=>{if(!Le.sel.ligands.some(ke=>ke.smiles===ce))return Le;const rt=Le.sel.ligands.map(ke=>ke.smiles===ce?{...ke,coord_atoms:ge}:ke);return Qe(Le,rt)}))}function q(ce,ge=!1){pe(Be=>{const Le=ge?[...Be.filter(rt=>!ce.some(ke=>ke.complex&&ke.complex===rt.complex)),...ce]:ce;return L(Le.slice(0,Tl).map(rt=>rt.token)),Le})}function re(ce){pe(ge=>ge.filter(Be=>Be.token!==ce)),L(ge=>ge.filter(Be=>Be!==ce))}function be(){pe([]),L([])}function Ae(ce){s(ge=>ge.filter((Be,Le)=>Le!==ce))}function Ke(){const ce=r.length;ce&&(v(r),s([]),ze(null),u(""),x(`${ce} complex${ce===1?"":"es"} removed.`))}function xt(){if(!_)return;const ce=_.length;s(_),v(null),x(`${ce} complex${ce===1?"":"es"} restored.`)}function Lt(){S.current=Date.now(),U(null),X(!0)}function it(){S.current!=null&&(U(Math.round((Date.now()-S.current)/1e3)),S.current=null,X(!1))}Q.useEffect(()=>{if(!D)return;const ce=setInterval(()=>Y(ge=>ge+1),1e3);return()=>clearInterval(ce)},[D]);const xn=D?y.jsxs(y.Fragment,{children:[y.jsx(tu,{name:"timer",size:13}),lg(Math.round((Date.now()-(S.current||Date.now()))/1e3))]}):H!=null?y.jsxs(y.Fragment,{children:[y.jsx(tu,{name:"timer",size:13}),"built in ",lg(H)]}):null;function Vn(ce){if(!ce)return;const ge=fC(ce);if(ge){u(ge);return}const Be=new FileReader;Be.onload=()=>{const Le=String(Be.result);if(/\u0000|�/.test(Le)){u("That file isn't plain text. Please upload a CSV.");return}i(Le),ue(Le)},Be.onerror=()=>u("Could not read that file."),Be.readAsText(ce)}async function ua(ce){if(o){if(V||P)return;try{J(!0),Lt();const ge=await St.submitJob([Gu(r[ce],o,l,d)],o,d,f);_e.current=ge.job_id,fe(ge.job_id),window.location.hash="job="+ge.job_id,te(`Build started: ${r[ce].name}.`),_r(ge.job_id,ge.estimate_s,0,!0)}catch(ge){it(),J(!1),z(y.jsx("span",{className:"pill-err",children:ge.message})),te(ge.message,!0)}return}if(!(V||P)){A(ce),E(!0),Lt(),te(`Building ${r[ce].name}…`);try{const ge=await St.build(Gu(r[ce],o,l,d),f);q(ge.results,!0);const Be=ge.results.length;te(`${r[ce].name} built: ${Be} structure${Be===1?"":"s"}.`)}catch(ge){z(y.jsx("span",{className:"pill-err",children:ge.message})),te(ge.message,!0)}finally{it(),A(null),E(!1)}}}function da(ce,ge){je(ce,{siteAssignment:ge}),ze(null)}async function fi(){if(V||P)return;const ce=r.filter(Le=>Le.supported&&!Le.needs_cap_selection),ge=r.filter(Le=>Le.needs_cap_selection).length,Be=ce.map(Le=>Gu(Le,o,l,d));if(!Be.length){const Le=ge?`No buildable complexes — ${ge} need their Cp/arene ring(s) selected as η-caps first (untick Donors).`:"None of these rows can be built. Fix the rows marked in red, then build again.";z(y.jsx("span",{className:"pill-err",children:Le})),te(Le,!0);return}try{J(!0),Lt();const Le=await St.submitJob(Be,o,d,f);_e.current=Le.job_id,fe(Le.job_id),window.location.hash="job="+Le.job_id;const rt=Be.length;te(`Build started: ${rt} complex${rt===1?"":"es"}.`+(ge?` ${ge} skipped (need η-cap selection).`:"")),_r(Le.job_id,Le.estimate_s,ge)}catch(Le){it(),J(!1),z(y.jsx("span",{className:"pill-err",children:Le.message})),te(Le.message,!0)}}async function _r(ce,ge,Be=0,Le=!1){_e.current=ce;const rt=async()=>{if(_e.current!==ce)return;let ke;try{ke=await St.getJob(ce)}catch{_e.current===ce&&setTimeout(rt,1500);return}if(_e.current!==ce)return;if(ke.detail)return J(!1),j(null),window.location.hash===`#job=${ce}`&&history.replaceState(null,"",window.location.pathname+window.location.search),te(ke.detail,!0),z(y.jsx("span",{className:"pill-err",children:ke.detail}));if(ke.status==="done"){it(),J(!1),j(null),_e.current=null;const W=ke.complex_errors||[];z(y.jsxs("div",{className:"job-bar",children:[y.jsxs("div",{className:"job-line",children:[y.jsxs("span",{className:"job-title",children:["Done — ",ke.results.length," structure",ke.results.length===1?"":"s"]}),W.length>0&&y.jsxs("span",{className:"pill-err",children:[W.length," failed"]}),Be>0&&y.jsxs("span",{className:"pill-warn",children:[Be," skipped (need η-cap selection)"]})]}),W.length>0&&y.jsx("ul",{className:"job-errs",children:W.map((B,de)=>y.jsxs("li",{children:[y.jsx("span",{className:"mono",children:B.complex||B.name||"complex"}),": ",B.error||"failed"]},de))})]})),q(ke.results,Le);const $=ke.results.length;te(`Build finished: ${$} structure${$===1?"":"s"}`+(W.length?`, ${W.length} failed`:"")+(Be?`, ${Be} skipped`:"")+"."),W.length&&console.warn("Build-all per-complex errors:",W);return}if(ke.status==="failed")return it(),J(!1),j(null),_e.current=null,ke.results&&ke.results.length&&q(ke.results,Le),te(`Build stopped: ${ke.error}`,!0),z(y.jsxs("span",{className:"pill-err",children:["Build stopped: ",ke.error]}));ke.results&&ke.results.length&&q(ke.results,Le);const At=ke.estimate_s||ge||0,Yt=At?Math.ceil(At/60):0,Yr=At>=600,pi=Math.round((ke.progress||0)*100),T=ke.results?ke.results.length:0,k=[`${pi}%`,Yt?`~${Yt} min`:"",T?`${T} ready`:"",Be?`${Be} skipped`:""].filter(Boolean).join(" · ");J(!0),fe(ce),j(ke.progress||0),z(y.jsxs("div",{className:"job-bar",children:[y.jsxs("div",{className:"job-line",children:[y.jsx("span",{className:"spinner"}),y.jsx("span",{className:"job-title",children:ke.stage||"Building…"}),y.jsx("span",{className:"job-meta",children:k})]}),y.jsxs("div",{className:"job-sub muted",children:[y.jsx("a",{href:`#job=${ce}`,children:"Keep this link"})," to return to your results",Yr?" — long job: safe to close the page, just don't resubmit":"","."]})]})),setTimeout(rt,1500)};rt()}async function ha(){const ce=Z||_e.current;if(ce){_e.current=null,z(y.jsxs(y.Fragment,{children:[y.jsx("span",{className:"spinner"})," Cancelling…"]}));try{await St.cancelJob(ce)}catch{}it(),J(!1),j(null),fe(null),z(y.jsx("span",{className:"pill-warn",children:"Build cancelled. Any completed structures are shown below."})),te("Build cancelled. Any completed structures are shown below."),window.location.hash.startsWith("#job=")&&history.replaceState(null,"",window.location.pathname+window.location.search)}}function fa(){z(""),_e.current=null,J(!1),j(null),fe(null),window.location.hash.startsWith("#job=")&&history.replaceState(null,"",window.location.pathname+window.location.search)}return Q.useEffect(()=>{const ce=window.location.hash.match(/job=([a-f0-9]+)/);ce&&_r(ce[1])},[]),y.jsxs(y.Fragment,{children:[y.jsx("img",{className:`floating-logo${ve&&Xe==null?" show":""}`,src:Vp,alt:"","aria-hidden":"true"}),y.jsxs("header",{ref:se,children:[y.jsxs("div",{className:"brand-row",children:[y.jsx("img",{className:"app-logo",src:Vp,alt:"MeCoBi logo"}),y.jsxs("div",{className:"brand",children:[y.jsxs("div",{className:"wordmark","aria-label":"MeCoBi",children:[y.jsx("span",{className:"cap",children:"M"}),"e",y.jsx("span",{className:"cap",children:"C"}),"o",y.jsx("span",{className:"cap",children:"B"}),"i"]}),y.jsxs("div",{className:"tagline",children:[y.jsx("span",{className:"cap",children:"M"}),"etal ",y.jsx("span",{className:"cap",children:"C"}),"omplex"," ",y.jsx("span",{className:"cap",children:"B"}),"uilder"]})]})]}),y.jsxs("div",{className:"header-right",children:[y.jsx("a",{className:"toggle-btn header-link",href:Hu,target:"_blank",rel:"noreferrer",children:"Paper"}),y.jsx("a",{className:"toggle-btn header-link",href:Vu,target:"_blank",rel:"noreferrer",children:"GitHub"}),y.jsx("a",{href:"https://thefreilab.com",target:"_blank",rel:"noreferrer",title:"TheFreiLab",children:y.jsx("img",{className:"freilab-logo",src:K,alt:"TheFreiLab"})}),y.jsxs("div",{className:"tour-btn-wrap",children:[y.jsx("button",{className:"toggle-btn"+(ee?" nudge":""),onClick:Pe,title:"Take a guided tour of the interface",children:"Tour"}),ee&&y.jsxs("div",{className:"tour-hint",role:"status",children:[y.jsx("span",{className:"tour-hint-icon","aria-hidden":"true",children:"🧭"}),y.jsxs("div",{className:"tour-hint-text",children:[y.jsx("strong",{children:"New here?"}),y.jsx("span",{children:"Take a quick guided tour."})]}),y.jsx("button",{className:"tour-hint-x","aria-label":"Dismiss",onClick:()=>Ie(!1),children:"×"})]})]}),y.jsx("button",{className:"toggle-btn",onClick:e,children:t==="dark"?"Light":"Dark"})]})]}),y.jsx(eS,{open:ne,steps:oC,actions:{loadSample:tt},onClose:()=>ae(!1)}),y.jsxs("main",{className:Xe!=null?"with-scene":"",children:[y.jsx("div",{className:"sr-only",role:"status",children:ie}),y.jsx("div",{className:"sr-only",role:"alert",children:ye}),y.jsxs("p",{className:"intro",children:[y.jsx("strong",{children:"MeCoBi"})," turns a metal, its oxidation state, and the SMILES of its ligands into optimised 3D structures. It assembles the coordination geometry, enumerates isomers, and optionally relaxes each with GFN2-xtb, quickly and at high throughput. Enter your complexes below, or load the sample to see the format."," ","If you use MeCoBi, please cite our"," ",y.jsx("a",{href:Hu,target:"_blank",rel:"noreferrer",children:"preprint"}),"; the code is open source on"," ",y.jsx("a",{href:Vu,target:"_blank",rel:"noreferrer",children:"GitHub"}),"."]}),y.jsx(sC,{}),y.jsxs("div",{className:"input-row"+(b?" with-library":""),children:[y.jsxs("div",{className:"card","data-tour":"input-card",children:[y.jsx("h2",{children:"Input"}),y.jsxs("label",{htmlFor:"csv",children:["One complex per line. A header row and the named-slot form (Name, Metal, Charge, L1…L6) both work — or click ",y.jsx("strong",{children:"Load sample"}),"."]}),y.jsx("div",{className:"csv-hint mono","aria-hidden":"true",children:"metal, oxidation_state, SMILES 1, SMILES 2, …"}),y.jsx("textarea",{ref:G,id:"csv",className:"csv-input",spellCheck:!1,value:n,onChange:ce=>i(ce.target.value)}),y.jsxs("div",{className:"row",style:{marginTop:12},children:[y.jsx("button",{className:"primary","data-tour":"parse-btn",onClick:()=>ue(),disabled:M,children:y.jsx(Qo,{busy:M,label:"Parse",busyLabel:"Parsing…",compact:!0})}),y.jsx("button",{type:"button",className:"ghost",title:"Upload a .csv file in the same format",onClick:()=>{var ce;return(ce=Re.current)==null?void 0:ce.click()},children:"Upload CSV"}),y.jsx("input",{ref:Re,type:"file",accept:".csv,text/csv,application/vnd.ms-excel",style:{display:"none"},tabIndex:-1,"aria-hidden":"true",onChange:ce=>{var ge;Vn((ge=ce.target.files)==null?void 0:ge[0]),ce.target.value=""}}),y.jsx("button",{className:"ghost","data-tour":"sample-btn",onClick:()=>i(aC),children:"Load sample"}),y.jsxs("button",{className:"ghost"+(b?" active":""),"data-tour":"ligand-library-btn",title:"Browse common ligands and click to insert their SMILES",onClick:()=>w(ce=>!ce),children:[y.jsx(tu,{name:"flask"}),"Ligand library"]}),y.jsx("span",{style:{marginLeft:"auto"},children:y.jsx(rC,{})})]}),M?y.jsx("div",{className:"progress indeterminate",style:{marginTop:10},title:"Parsing…",role:"progressbar","aria-label":"Parsing",children:y.jsx("div",{className:"progress-fill"})}):null,y.jsxs("div",{className:"muted status-line",role:"status",children:[g,_?y.jsx("button",{type:"button",className:"ghost undo-btn",onClick:xt,children:"Undo"}):null]}),y.jsx("div",{className:"status-line",role:"alert",children:m?y.jsx("span",{className:"pill-err",children:m}):null})]}),b&&y.jsx(YA,{onInsert:Se,onClose:()=>w(!1)})]}),r.length===0&&I&&y.jsx("div",{children:I}),r.length>0&&y.jsxs("div",{className:"hub-row",children:[y.jsx(Wy,{rows:r,onRowChange:je,onDonorsChange:F,onApplyDonorsToAll:xe,onBuild:ua,onRemoveRow:Ae,onRemoveAllRows:Ke,onAssign:ze,buildingIndex:C,building:P,onBuildAll:fi,jobStatus:I,timerText:xn,jobRunning:V,jobProgress:N,canCancel:V&&!!Z,onCancelJob:ha,onDismissJob:fa,relax:o,setRelax:a,spin:l,setSpin:c,maxOptTime:d,setMaxOptTime:h,advOptions:f,setAdvOptions:p,optionGroups:o0,advDefaults:og}),Xe!=null&&r[Xe]&&y.jsx(XA,{complex:r[Xe],geometry:r[Xe].sel.geometry,onClose:()=>ze(null),onBuild:ce=>da(Xe,ce)},`${Xe}:${r[Xe].sel.geometry}`)]}),y.jsx(iC,{files:me,viewTokens:Ue,onViewTokens:L,onRemove:re,onRemoveAll:be})]}),y.jsxs("footer",{className:"mono muted",style:{textAlign:"center",padding:"18px 0 26px",fontSize:"var(--text-caption)"},children:[y.jsx(Zy,{refreshKey:me.length}),y.jsx("a",{href:"https://www.york.ac.uk/about/legal-statements/",target:"_blank",rel:"noreferrer",children:"Disclaimer"})," · ",y.jsx("a",{href:Hu,target:"_blank",rel:"noreferrer",children:"Preprint"})," · ",y.jsx("a",{href:Vu,target:"_blank",rel:"noreferrer",children:"GitHub"}),$e?` · MeCoBi v${$e.version}`+($e.branch?` · ${$e.branch}`:"")+($e.commit?` @ ${$e.commit}`:"")+($e.updated?` · last updated ${dC($e.updated)}`:""):""]})]})}Mv(document.getElementById("root")).render(y.jsx(E0.StrictMode,{children:y.jsx(gC,{})}));
