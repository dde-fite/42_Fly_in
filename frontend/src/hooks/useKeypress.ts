import { useEffect, useRef } from "react";

interface KeypressOptions {
	ctrl?: boolean;
	alt?: boolean;
	preventDefault?: boolean;
}

export default function useKeypress(
	key: string,
	action: (e: KeyboardEvent) => void,
	options: KeypressOptions = {},
) {
	const actionRef = useRef(action);
	const { ctrl, alt, preventDefault } = options;

	useEffect(() => {
		actionRef.current = action;
	}, [action]);

	useEffect(() => {
		function onKeyDown(e: KeyboardEvent) {
			if (e.repeat) return;
			const target = e.target as HTMLElement;
			if (target.tagName === "INPUT" || target.tagName === "TEXTAREA") return;
			if (e.key !== key) return;
			if (ctrl !== undefined && e.ctrlKey !== ctrl) return;
			if (alt !== undefined && e.altKey !== alt) return;
			if (preventDefault) e.preventDefault();
			actionRef.current(e);
		}

		window.addEventListener("keydown", onKeyDown);
		return () => window.removeEventListener("keydown", onKeyDown);
	}, [key, ctrl, alt, preventDefault]);
}
