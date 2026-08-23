"use client";
import { useCallback, useSyncExternalStore } from "react";

/**
 * Раньше здесь было три проблемы:
 *  - removeEventListener получал не ту функцию (addEventListener вешал
 *    свежую обёртку debounce), поэтому слушатель не снимался никогда;
 *  - эффект зависел от matches и на каждое изменение вешал ещё один
 *    слушатель поверх старых;
 *  - debounce в 300 мс задерживал реакцию на поворот экрана.
 * useSyncExternalStore подписывается один раз и корректно отписывается.
 */
const useMediaQuery = (query: string): boolean => {
  const subscribe = useCallback(
    (onChange: () => void) => {
      if (typeof window === "undefined") return () => {};
      const media = window.matchMedia(query);
      media.addEventListener("change", onChange);
      return () => media.removeEventListener("change", onChange);
    },
    [query]
  );

  const getSnapshot = useCallback(() => {
    if (typeof window === "undefined") return false;
    return window.matchMedia(query).matches;
  }, [query]);

  // На сервере разметки нет — считаем, что это десктоп,
  // клиент поправит значение сразу после гидрации.
  const getServerSnapshot = useCallback(() => false, []);

  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
};

export default useMediaQuery;
