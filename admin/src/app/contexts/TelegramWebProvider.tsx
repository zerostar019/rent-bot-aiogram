import Script from "next/script";
// export interface ITelegramContext {
//   webApp?: IWebApp;
//   user?: ITelegramUser;
// }

// export const TelegramContext = createContext<ITelegramContext>({});

export const TelegramProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  // const [webApp, setWebApp] = useState<IWebApp | null>(null);

  // useEffect(() => {
  //   const app = (window as any).Telegram?.WebApp;
  //   if (app) {
  //     app.ready();
  //     setWebApp(app);
  //   }
  // }, []);

  // const value = useMemo(() => {
  //   return webApp
  //     ? {
  //         webApp,
  //         unsafeData: webApp.initDataUnsafe,
  //         user: webApp.initDataUnsafe.user,
  //       }
  //     : {};
  // }, [webApp]);

  return (
    <>
      <Script
        src="https://telegram.org/js/telegram-web-app.js"
        strategy="beforeInteractive"
      />{" "}
      {children}
    </>
  );
};

// export const useTelegram = () => useContext(TelegramContext);
