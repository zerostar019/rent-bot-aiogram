import BackgroundWrapper from "./components/BackgroundWrapper/BackgroundWrapper";
import BookingForm from "./components/BookingForm/BookingForm";
import styles from "./styles.module.css";
import { useEffect, useState } from "react";
import { UserDataInterface } from "./types";
import { App } from "antd";

function Main() {
  const [userData, setUserData] = useState<UserDataInterface>({
    userId: undefined,
    queryId: undefined,
  });
  useEffect(() => {
    Telegram.WebApp.ready();
    Telegram.WebApp.requestFullscreen();
    Telegram.WebApp.MainButton.text = "Выберите даты";
    Telegram.WebApp.MainButton.disable();
    Telegram.WebApp.MainButton.color = "#dcdcdc";
    Telegram.WebApp.MainButton.show();
    Telegram.WebApp.lockOrientation();
    Telegram.WebApp.MainButton.hasShineEffect = false;
    const userData = Telegram.WebApp.initDataUnsafe;
    setUserData({
      userId: userData.user?.id,
      queryId: userData.query_id,
    });
  }, []);

  return (
    <App>
      <BackgroundWrapper>
        <div className={styles["page"]}>
          <BookingForm userData={userData} />
        </div>
      </BackgroundWrapper>
    </App>
  );
}

export default Main;
