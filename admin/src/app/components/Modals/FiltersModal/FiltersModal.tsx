import { Modal } from "antd";
import { Dispatch, SetStateAction } from "react";
import Filter from "../../Pages/Bookings/Filter/Filter";

const FiltersModal = ({
  open,
  setOpen,
}: {
  open: boolean;
  setOpen: Dispatch<SetStateAction<boolean>>;
}) => {
  return (
    <Modal
      centered
      footer={() => null}
      open={open}
      onCancel={() => setOpen(false)}
      onClose={() => setOpen(false)}
    >
      <Filter setClose={setOpen} />
    </Modal>
  );
};

export default FiltersModal;
