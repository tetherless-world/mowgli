package models.graphql

import io.github.tetherlessworld.twxplore.lib.base.models.graphql.BaseGraphQlSchemaDefinition
import models.cskg.{Edge, Node}
import sangria.schema.{Argument, Field, IntType, ListType, ObjectType, OptionType, Schema, StringType, fields}
import sangria.macros.derive._

object GraphQlSchemaDefinition extends BaseGraphQlSchemaDefinition {
  // Object types
  implicit val EdgeType = deriveObjectType[GraphQlSchemaContext, Edge]()
  implicit val NodeType = deriveObjectType[GraphQlSchemaContext, Node]()

  // Query types
  val RootQueryType = ObjectType("RootQuery",  fields[GraphQlSchemaContext, Unit](
    Field("matchingNodes", ListType(NodeType), arguments = LimitArgument :: OffsetArgument :: TextArgument :: Nil, resolve = ctx => ctx.ctx.store.getMatchingNodes(limit = ctx.args.arg(LimitArgument), offset = ctx.args.arg(OffsetArgument), text = ctx.args.arg(TextArgument))),
    Field("matchingNodesCount", IntType, arguments = TextArgument :: Nil, resolve = ctx => ctx.ctx.store.getMatchingNodesCount(text = ctx.args.arg(TextArgument)))
  ))

  // Schema
  val schema = Schema(
    RootQueryType
  )
}