// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import DetailsDialog from "../common/DetailsDialog";
import { Contact } from "../contacts/types";

interface UserPersonaDialogProps {
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
  userPersona: Contact | null;
}

const UserPersonaDialog = ({
  isOpen,
  setIsOpen,
  userPersona,
}: UserPersonaDialogProps) => {
  if (!userPersona) return null;

  return (
    <DetailsDialog
      isOpen={isOpen}
      onClose={() => setIsOpen(false)}
      title="User Persona"
      properties={{
        ID: userPersona.contact_id,
        "First Name": userPersona.first_name,
        "Last Name": userPersona.last_name,
        Gender: userPersona.gender,

        Age: userPersona.age,
        Nationality: userPersona.nationality,
        City: userPersona.city_living,
        Country: userPersona.country,
        Status: userPersona.status,
        Job: userPersona.job,
        Description: userPersona.description,
        Email: userPersona.email,
        Phone: userPersona.phone,
        Address: userPersona.address,
      }}
    />
  );
};

export default UserPersonaDialog;
