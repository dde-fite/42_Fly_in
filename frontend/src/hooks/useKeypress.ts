import { useEffect, useRef } from "react";
/**
 * useKeyPress
 * @param {string} key - the name of the key to respond to, compared against event.key
 * @param {function} action - the action to perform on key press
 */
export default function useKeypress(key, action) {
  const actionRef = useRef(action);

  useEffect(() => {
    actionRef.current = action;
  }, [action]);

  useEffect(() => {
    function onKeyup(e) {
      if (e.key === key) {
        actionRef.current();
      }
    }

    window.addEventListener("keyup", onKeyup);
    return () => window.removeEventListener("keyup", onKeyup);
  }, [key]);
}