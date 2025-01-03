"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    """The schema upgrade script for this revision."""
    ${upgrades if upgrades else "pass  # pylint: disable=unnecessary-pass"}


def downgrade() -> None:
    """The schema downgrade script for this revision."""
    ${downgrades if downgrades else "pass  # pylint: disable=unnecessary-pass"}
