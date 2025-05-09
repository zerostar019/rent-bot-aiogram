import React from "react";
import styles from "./styles.module.css";

const BackgroundWrapper = ({ children }: { children: React.ReactNode }) => {
  return (
    <>
      <div
      className={styles['content']}
      >
        {children}
      </div>
      <div className={styles["layout"]}>
        <div className={styles["gradients-container"]}>
          <div className={styles["g1"]}></div>
          <div className={styles["g2"]}></div>
          <div className={styles["g3"]}></div>
          <div className={styles["g4"]}></div>
          <div className={styles["g5"]}></div>
          <div className={styles["interactive"]}></div>
        </div>
      </div>
    </>
  );
};

export default BackgroundWrapper;
