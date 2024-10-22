import { MinoriBaseAPI } from './base.js'
import { build_error } from '../common.js';
import { AuthorAlias, FullAuthorAlias, Pagination } from '../models.js';

class MinoriAuthorAliasesAPI extends MinoriBaseAPI {
  async get_page(page = 1) {
    const resp = await fetch(this.build_url('/authoraliases', { page }))

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to get author aliases');
    }

    const json = await resp.json();
    return {
      authors: json.author_aliases.map(i => new AuthorAlias(i)),
      pagination: new Pagination(json.pagination)
    };
  }

  async get_one(authoralias_id) {
    authoralias_id = encodeURIComponent(authoralias_id);
    const resp = await fetch(this.build_url(`/authoraliases/${authoralias_id}`))

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to get author alias');
    }

    return new FullAuthorAlias((await resp.json()).author_alias);
  }

  async update_name(authoralias_id, name) {
    authoralias_id = encodeURIComponent(authoralias_id);
    const resp = await fetch(this.build_url(`/authoraliases/${authoralias_id}`), {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to update author alias name');
    }

    return new FullAuthorAlias((await resp.json()).author_alias);
  }

  async delete(authoralias_id) {
    authoralias_id = encodeURIComponent(authoralias_id);
    const resp = await fetch(this.build_url(`/authoraliases/${authoralias_id}`), {
      method: 'DELETE'
    })

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to delete author alias');
    }
  }

  async reassign_author_alias(authoralias_id, new_parent_author_id) {
    authoralias_id = encodeURIComponent(authoralias_id);
    new_parent_author_id = encodeURIComponent(new_parent_author_id);
    const resp = await fetch(this.build_url(`/authoraliases/${authoralias_id}/reassign/${new_parent_author_id}`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to reassign author alias');
    }

    return new FullAuthorAlias((await resp.json()).author_alias);
  }
}

export { MinoriAuthorAliasesAPI };
